import random
import re
import os
import sys
from datetime import datetime, timedelta
import json
import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from config.config import DB_CONFIG
from src.edi.generator import HEALTH_PLANS, generate_id
from mimesis import Person

person = Person('en')


class EDIParser:
    def __init__(self):
        self.segment_delimiter = '~'
        self.element_delimiter = '*'
        self.conn = None
        self.cursor = None

    def connect_db(self):
        """建立数据库连接"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            print("数据库连接成功")
        except Error as e:
            print(f"数据库连接错误: {e}")
            raise

    def close_db(self):
        """关闭数据库连接"""
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            print("数据库连接已关闭")

    def parse_edi_file(self, file_path: str) -> List[Dict]:
        """解析EDI文件为段列表"""
        segments = []
        with open(file_path, 'r') as f:
            content = f.read()
            for segment in content.split(self.segment_delimiter):
                segment = segment.strip()
                if segment:
                    elements = segment.split(self.element_delimiter)
                    segment_id = elements[0]
                    segments.append({
                        'segment_id': segment_id,
                        'elements': elements[1:],
                        'raw': segment
                    })
        return segments

    def parse_edi_834(self, file_path: str):
        """解析EDI 834文件并插入数据库"""
        print(f"开始解析EDI 834文件: {file_path}")
        segments = self.parse_edi_file(file_path)

        # 先记录EDI交易
        transaction_id = self.record_edi_transaction('834', file_path)

        # 解析会员和注册信息
        members = []
        current_member = None

        for segment in segments:
            try:
                if segment['segment_id'] == 'INS':
                    # 开始新会员记录
                    if current_member:
                        members.append(current_member)
                    current_member = {
                        'coverage_status': segment['elements'][3] if len(segment['elements']) > 3 else None,
                        'medicare_plan': segment['elements'][4] if len(segment['elements']) > 4 and segment['elements'][
                            4] else None,
                        'refs': [],
                        'demographics': None,
                        'address': {},
                        'enrollment': {},
                        'termination_reason': None
                    }
                elif segment['segment_id'] == 'REF' and current_member:
                    ref_type = segment['elements'][0] if len(segment['elements']) > 0 else None
                    ref_value = segment['elements'][1] if len(segment['elements']) > 1 else None
                    if ref_type == 'SY':  # SSN
                        current_member['ssn'] = ref_value
                    current_member['refs'].append({
                        'type': ref_type,
                        'value': ref_value
                    })
                elif segment['segment_id'] == 'NM1' and segment['elements'][0] == 'IL' and current_member:
                    # 会员姓名信息
                    current_member.update({
                        'last_name': segment['elements'][2],
                        'first_name': segment['elements'][3],
                        'middle_initial': segment['elements'][5] if len(segment['elements']) > 5 else '',
                        'member_id': segment['elements'][8] if len(segment['elements']) > 8 else None
                    })
                elif segment['segment_id'] == 'DMG' and current_member:
                    # 人口统计信息
                    dob_str = segment['elements'][1] if len(segment['elements']) > 1 else None
                    dob = datetime.strptime(dob_str, '%Y%m%d').date() if dob_str and segment['elements'][
                        0] == 'D8' else None
                    current_member['demographics'] = {
                        'dob': dob,
                        'gender': segment['elements'][2] if len(segment['elements']) > 2 else None
                    }
                elif segment['segment_id'] == 'N3' and current_member:
                    # 地址信息 - 街道
                    current_member['address']['street'] = segment['elements'][0] if segment['elements'] else ''
                elif segment['segment_id'] == 'N4' and current_member:
                    # 地址信息 - 城市、州、邮编
                    if len(segment['elements']) >= 3:
                        current_member['address'].update({
                            'city': segment['elements'][0],
                            'state': segment['elements'][1],
                            'zip': segment['elements'][2]
                        })
                elif segment['segment_id'] == 'PER' and current_member:
                    # 联系方式
                    for i in range(0, len(segment['elements']), 2):
                        comm_type = segment['elements'][i] if len(segment['elements']) > i else None
                        comm_value = segment['elements'][i + 1] if len(segment['elements']) > i + 1 else None
                        if comm_type == 'EM':
                            current_member['email'] = comm_value
                        elif comm_type == 'HP':
                            current_member['phone'] = comm_value
                elif segment['segment_id'] == 'HD' and current_member:
                    # 健康计划信息
                    if len(segment['elements']) > 3:
                        current_member['enrollment']['plan_id'] = segment['elements'][3]
                    if len(segment['elements']) > 1:
                        current_member['enrollment']['insurance_line'] = segment['elements'][1]
                elif segment['segment_id'] == 'DTP' and current_member and current_member.get('enrollment'):
                    # 日期信息
                    if segment['elements'][0] == '356' and len(segment['elements']) > 2:  # 开始日期
                        date_str = segment['elements'][2] if segment['elements'][1] == 'D8' else None
                        if date_str:
                            try:
                                current_member['enrollment']['start_date'] = datetime.strptime(date_str,
                                                                                               '%Y%m%d').date()
                            except ValueError:
                                current_member['enrollment']['start_date'] = None
                    elif segment['elements'][0] == '357' and len(segment['elements']) > 2:  # 结束日期
                        date_str = segment['elements'][2] if segment['elements'][1] == 'D8' else None
                        if date_str:
                            try:
                                current_member['enrollment']['end_date'] = datetime.strptime(date_str, '%Y%m%d').date()
                            except ValueError:
                                current_member['enrollment']['end_date'] = None
                # 处理终止原因
                elif segment['segment_id'] == 'INS' and len(segment['elements']) > 3 and segment['elements'][3] == 'T':
                    if len(segment['elements']) > 4:
                        current_member['termination_reason'] = segment['elements'][4]
            except Exception as e:
                print(f"解析段时出错: {segment['raw']}, 错误: {str(e)}")
                continue

        # 添加最后一个会员
        if current_member:
            members.append(current_member)

        # 插入数据库
        processed_count = 0
        for member in members:
            try:
                # 1. 确定会员ID
                member_id = member.get('member_id')
                if not member_id:
                    # 尝试从REF段获取会员ID
                    for ref in member.get('refs', []):
                        if ref['type'] == '0F':
                            member_id = ref['value']
                            break

                if not member_id:
                    print("无法确定会员ID，跳过此记录")
                    continue

                # 2. 准备地址数据
                address_data = member.get('address', {})
                address_json = json.dumps(address_data) if address_data else None

                # 3. 检查会员是否已存在
                self.cursor.execute("SELECT id FROM members WHERE id = %s", (member_id,))
                existing_member = self.cursor.fetchone()

                if not existing_member:
                    # 插入新会员
                    insert_member = """
                    INSERT INTO members (id, last_name, first_name, dob, gender, coverage_status, address, phone, 
                                        email, ssn, medicare_plan, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    self.cursor.execute(insert_member, (
                        member_id,
                        member.get('last_name', ''),
                        member.get('first_name', ''),
                        member['demographics']['dob'] if member.get('demographics') else None,
                        member['demographics']['gender'] if member.get('demographics') else None,
                        member.get('coverage_status'),
                        address_json,
                        member.get('phone'),
                        member.get('email'),
                        member.get('ssn'),
                        member.get('medicare_plan')
                    ))
                    print(f"插入会员: {member_id}")

                # 4. 处理注册信息
                if member.get('enrollment', {}).get('plan_id'):
                    plan_id = member['enrollment']['plan_id']

                    # 检查健康计划是否存在
                    self.cursor.execute("SELECT plan_id FROM health_plans WHERE plan_id = %s", (plan_id,))
                    if not self.cursor.fetchone():
                        # 查找对应的健康计划数据
                        plan_data = None
                        for plan in HEALTH_PLANS:
                            if plan['id'] == plan_id:
                                plan_data = plan
                                break

                        if plan_data:
                            # 插入健康计划数据
                            insert_plan = """
                                INSERT INTO health_plans (plan_id, plan_name, plan_type, monthly_premium, annual_deductible, 
                                                        coinsurance_rate, out_of_pocket_max, features, description, effective_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                            features_json = json.dumps(plan_data['features'])
                            self.cursor.execute(insert_plan, (
                                plan_data['id'],
                                plan_data['name'],
                                plan_data['type'],
                                plan_data['premium'],
                                plan_data['deductible'],
                                plan_data['coinsurance'],
                                plan_data['oop_max'],
                                features_json,
                                plan_data['description'],
                                datetime.now().date()
                            ))
                            print(f"插入健康计划: {plan_id}")
                            self.conn.commit()  # 提交健康计划插入
                        else:
                            print(f"找不到健康计划数据: {plan_id}")
                            continue  # 跳过此会员记录
                    # 插入注册记录
                    enrollment_id = f"ENR{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
                    status = 'ACTIVE' if not member['enrollment'].get('end_date') else 'TERMINATED'

                    insert_enrollment = """
                    INSERT INTO enrollments (id, member_id, plan_id, sponsor_id, start_date, end_date, 
                                            relationship_code, status, transaction_type, insurance_line,
                                            termination_reason, action_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    self.cursor.execute(insert_enrollment, (
                        enrollment_id,
                        member_id,
                        plan_id,
                        'DEFAULTSPO',  # 默认赞助商ID
                        member['enrollment'].get('start_date'),
                        member['enrollment'].get('end_date'),
                        '18',  # 本人
                        status,
                        '021',  # 新增
                        member['enrollment'].get('insurance_line'),
                        member.get('termination_reason'),
                        "2"
                    ))
                    print(f"插入注册记录: {enrollment_id} 为会员 {member_id}")

                self.conn.commit()
                processed_count += 1
            except Error as e:
                print(f"数据库插入错误: {e}")
                self.conn.rollback()

        # 更新EDI交易状态
        self.update_edi_transaction_status(transaction_id, 'PROCESSED', processed_count)
        print(f"EDI 834文件解析完成，处理了 {processed_count} 条会员记录")

    def parse_edi_837(self, file_path: str):
        """解析EDI 837文件并插入数据库 - 增强版本"""
        print(f"开始解析EDI 837文件: {file_path}")
        segments = self.parse_edi_file(file_path)

        # 先记录EDI交易
        transaction_id = self.record_edi_transaction('837', file_path)

        # 解析索赔信息
        claims = []
        current_claim = None
        current_provider = None
        current_member = None
        current_diagnoses = []
        current_service_lines = []
        current_hl_level = None
        pending_nm1_segments = []
        current_service_line = None  # 初始化服务行变量

        for segment in segments:
            try:
                if segment['segment_id'] == 'HL':
                    # 开始新的HL层次
                    current_hl_level = segment['elements'][3] if len(segment['elements']) > 3 else None
                    if current_claim:
                        claims.append({
                            'claim': current_claim,
                            'provider': current_provider,
                            'member': current_member,
                            'diagnoses': current_diagnoses,
                            'service_lines': current_service_lines
                        })

                    # 重置当前变量
                    current_claim = None
                    current_provider = None
                    current_member = None
                    current_diagnoses = []
                    current_service_lines = []
                    current_service_line = None
                    pending_nm1_segments = []
                    pending_n3_segments = []
                    pending_n4_segments = []

                elif segment['segment_id'] == 'CLM':
                    # 索赔基本信息
                    current_claim = {
                        'claim_id': segment['elements'][0],
                        'billed_amount': float(segment['elements'][1]) if segment['elements'][1] else 0.0,
                        'status': 'RECEIVED',
                        'claim_type': 'MEDICAL',
                        'service_date': None,
                        'submission_date': datetime.now().date(),
                        'procedure_code': None,
                        'claim_frequency_code': segment['elements'][5] if len(segment['elements']) > 5 else '1',
                        'claim_source_code': segment['elements'][6][0] if len(segment['elements']) > 6 and
                                                                          segment['elements'][6] else '01',
                        'facility_type_code': segment['elements'][8] if len(segment['elements']) > 8 else '11',
                        'location_type': self.map_facility_type(segment['elements'][8]) if len(
                            segment['elements']) > 8 else 'OFFICE',
                        'is_duplicate': 0,
                        'fraud_score': None,
                        'notes': None
                    }

                    # 处理之前缓存的NM1段
                    for nm1_segment in pending_nm1_segments:
                        if nm1_segment['elements'][0] == '85' and current_claim:
                            # 提供者信息
                            current_provider = {
                                'last_name': nm1_segment['elements'][2] if len(nm1_segment['elements']) > 2 else '',
                                'first_name': nm1_segment['elements'][3] if len(nm1_segment['elements']) > 3 else '',
                                'npi': nm1_segment['elements'][7] if len(nm1_segment['elements']) > 7 else None,
                                'provider_type': 'INDIVIDUAL',
                                'specialty': 'Family Practice',
                                'tax_id': generate_id("TAX", 9),
                                'address': {},
                                'phone': person.telephone(),
                                'email': person.email(),
                                'is_in_network': True
                            }
                        elif nm1_segment['elements'][0] == 'IL' and current_claim:
                            # 会员信息
                            current_member = {
                                'last_name': nm1_segment['elements'][2] if len(nm1_segment['elements']) > 2 else '',
                                'first_name': nm1_segment['elements'][3] if len(nm1_segment['elements']) > 3 else '',
                                'member_id': nm1_segment['elements'][7] if len(nm1_segment['elements']) > 7 else None
                            }

                    for n3_segment in pending_n3_segments:
                        if n3_segment['segment_id'] == 'N3':
                            if current_provider:
                                current_provider['address']['street'] = segment['elements'][0] if segment[
                                    'elements'] else ''

                    for n4_segment in pending_n4_segments:
                        if current_provider:
                            if len(n4_segment['elements']) >= 3:
                                current_provider['address'].update({
                                    'city': segment['elements'][0],
                                    'state': segment['elements'][1],
                                    'zip': segment['elements'][2]
                                })

                    pending_nm1_segments = []
                    pending_n3_segments = []
                    pending_n4_segments = []

                elif segment['segment_id'] == 'NM1':
                    if current_claim:
                        if segment['elements'][0] == '85' and current_claim:
                            current_provider = {
                                'last_name': segment['elements'][2] if len(segment['elements']) > 2 else '',
                                'first_name': segment['elements'][3] if len(segment['elements']) > 3 else '',
                                'npi': segment['elements'][7] if len(segment['elements']) > 7 else None,
                                'provider_type': 'INDIVIDUAL',
                                'specialty': 'Family Practice',
                                'tax_id': None,
                                'address': {},
                                'phone': None,
                                'email': None,
                                'is_in_network': True
                            }
                        elif segment['elements'][0] == 'IL' and current_claim:
                            current_member = {
                                'last_name': segment['elements'][2] if len(segment['elements']) > 2 else '',
                                'first_name': segment['elements'][3] if len(segment['elements']) > 3 else '',
                                'member_id': segment['elements'][7] if len(segment['elements']) > 7 else None
                            }
                    else:
                        pending_nm1_segments.append(segment)

                elif segment['segment_id'] == 'PRV' and current_provider:
                    if len(segment['elements']) > 3:
                        current_provider['specialty'] = segment['elements'][3].replace("^", " ") if "^" in \
                                                                                                    segment['elements'][
                                                                                                        3] else \
                            segment['elements'][3]

                elif segment['segment_id'] == 'DMG' and current_member:
                    dob_str = segment['elements'][1] if len(segment['elements']) > 1 else None
                    current_member['dob'] = datetime.strptime(dob_str, '%Y%m%d').date() if dob_str and \
                                                                                           segment['elements'][
                                                                                               0] == 'D8' else None
                    current_member['gender'] = segment['elements'][2] if len(segment['elements']) > 2 else None

                elif segment['segment_id'] == 'N3':
                    if current_provider:
                        current_provider['address']['street'] = segment['elements'][0] if segment['elements'] else ''
                    else:
                        pending_n3_segments.append(segment)


                elif segment['segment_id'] == 'N4':
                    if current_provider:
                        if len(segment['elements']) >= 3:
                            current_provider['address'].update({
                                'city': segment['elements'][0],
                                'state': segment['elements'][1],
                                'zip': segment['elements'][2]
                            })
                    else:
                        pending_n4_segments.append(segment)

                elif segment['segment_id'] == 'PER' and current_provider:
                    for i in range(0, len(segment['elements']), 2):
                        comm_type = segment['elements'][i] if len(segment['elements']) > i else None
                        comm_value = segment['elements'][i + 1] if len(segment['elements']) > i + 1 else None
                        if comm_type == 'TE':
                            current_provider['phone'] = comm_value
                        elif comm_type == 'EM':
                            current_provider['email'] = comm_value

                elif segment['segment_id'] == 'HI' and current_claim:
                    for diag_code in segment['elements']:
                        if diag_code.startswith('ABK:'):
                            diagnosis_code = diag_code[4:]
                            current_diagnoses.append({
                                'diagnosis_code': diagnosis_code,
                                'diagnosis_description': f"Diagnosis {diagnosis_code}",
                                'clinical_status': 'ACTIVE',
                                'verification_status': 'CONFIRMED',
                                'recorded_date': datetime.now(),
                                'category': 'PRIMARY' if len(current_diagnoses) == 0 else 'SECONDARY',
                                'severity': random.choice(['MILD', 'MODERATE', 'SEVERE']),
                                'notes': random.choice(
                                    ['Patient reported symptoms', 'Diagnosed during routine check', 'Referred by PCP'])
                            })
                        elif segment['elements'][0].startswith('ABF:'):  # 发病日期
                            if current_diagnoses:
                                onset_date = segment['elements'][0][4:]
                                current_diagnoses[-1]['onset_date'] = datetime.strptime(onset_date, '%Y%m%d').date()
                        elif segment['elements'][0].startswith('ABJ:'):  # 诊断描述
                            if current_diagnoses:
                                current_diagnoses[-1]['diagnosis_description'] = segment['elements'][0][4:]

                elif segment['segment_id'] == 'DTP' and len(segment['elements']) > 2 and current_claim:
                    if segment['elements'][0] == '472':  # 服务日期
                        date_str = segment['elements'][2] if segment['elements'][1] == 'D8' else None
                        if date_str:
                            try:
                                current_claim['service_date'] = datetime.strptime(date_str, '%Y%m%d').date()
                            except ValueError:
                                current_claim['service_date'] = None

                elif segment['segment_id'] == 'LX' and current_claim:
                    # 服务行开始 - 先保存前一个服务行(如果有)
                    if current_service_line:
                        current_service_lines.append(current_service_line)
                    # 服务行开始
                    current_service_line = {
                        'procedure_code': None,
                        'billed_amount': 0.0,
                        'service_date': current_claim['service_date'],
                        'units': 1,
                        'diagnosis_code': current_diagnoses[0]['diagnosis_code'] if current_diagnoses else None,
                        'modifier_code': None,
                        'place_of_service': '11',
                        'charge_amount': 0.0  # 新增字段
                    }

                elif segment['segment_id'] == 'SV1' and current_claim and current_service_line:
                    proc_code = segment['elements'][0][3:] if segment['elements'][0].startswith('HC:') else \
                        segment['elements'][0]
                    if ':' in proc_code:  # 处理修饰符
                        proc_code, modifier = proc_code.split(':')
                        current_service_line['modifier_code'] = modifier

                    billed_amt = float(segment['elements'][1]) if len(segment['elements']) > 1 and segment['elements'][
                        1] else 0.0
                    units = int(segment['elements'][3]) if len(segment['elements']) > 3 and segment['elements'][
                        3] else 1

                    current_service_line.update({
                        'procedure_code': proc_code,
                        'billed_amount': billed_amt,
                        'units': units,
                        'procedure_description': self.map_procedure_code(proc_code),
                        'charge_amount': billed_amt * 1.1  # 假设收费金额比账单金额高10%
                    })

                    if not current_claim['procedure_code']:
                        current_claim['procedure_code'] = proc_code

                elif segment['segment_id'] == 'REF' and current_service_line:
                    if len(segment['elements']) > 1 and segment['elements'][0] == '6R':  # 服务地点
                        current_service_line['place_of_service'] = segment['elements'][1]

                # elif segment['segment_id'] == 'SVC' and current_claim and current_service_line:
                #     # 服务行完成
                #     current_service_lines.append(current_service_line)
                #     current_service_line = None

                # 在HL段结束时添加服务行到列表
                # if segment['segment_id'] == 'HL' and current_service_line:
                #     current_service_lines.append(current_service_line)
                #     current_service_line = None
            except Exception as e:
                print(f"解析段时出错: {segment['raw']}, 错误: {str(e)}")
                continue

        # 添加最后一个服务行(如果有)
        if current_service_line:
            current_service_lines.append(current_service_line)
            current_service_line = None
        # 添加最后一个索赔记录
        if current_claim:
            claims.append({
                'claim': current_claim,
                'provider': current_provider,
                'member': current_member,
                'diagnoses': current_diagnoses,
                'service_lines': current_service_lines
            })

        # 插入数据库
        processed_count = 0
        for claim_data in claims:
            try:
                # 1. 检查会员是否存在
                member_id = claim_data['member']['member_id']
                if not member_id:
                    print("无法确定会员ID，跳过此索赔记录")
                    continue

                self.cursor.execute("SELECT id FROM members WHERE id = %s", (member_id,))
                if not self.cursor.fetchone():
                    print(f"会员 {member_id} 不存在，跳过此索赔记录")
                    continue

                # 2. 处理提供者信息
                provider_npi = claim_data['provider']['npi']
                provider_id = None

                if provider_npi:
                    self.cursor.execute("SELECT id FROM providers WHERE npi = %s", (provider_npi,))
                    provider = self.cursor.fetchone()

                    if not provider:
                        # 生成唯一提供者ID
                        provider_id = f"PROV{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
                        insert_provider = """
                                        INSERT INTO providers (id, npi, legal_name, doing_business_as, provider_type, specialty, tax_id, 
                                                            address, phone, email, is_in_network, contracts, created_at, updated_at)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                                        """
                        self.cursor.execute(insert_provider, (
                            provider_id,
                            provider_npi,
                            f"{claim_data['provider']['first_name']} {claim_data['provider']['last_name']}",
                            claim_data['provider'].get('doing_business_as', ''),
                            claim_data['provider']['provider_type'],
                            claim_data['provider'].get('specialty', 'Family Practice'),
                            claim_data['provider'].get('tax_id', generate_id("TAX", 9)),
                            json.dumps(claim_data['provider'].get('address', {})),
                            claim_data['provider'].get('phone', person.telephone()),
                            claim_data['provider'].get('email', person.email()),
                            claim_data['provider'].get('is_in_network', True),
                            claim_data['provider'].get('contracts', json.dumps({"default": True}))
                        ))
                        print(f"插入新提供者: {provider_id}")
                    else:
                        provider_id = provider['id']

                if not provider_id:
                    print("无法确定提供者ID，跳过此索赔记录")
                    continue

                # 3. 获取会员的当前注册记录
                self.cursor.execute("""
                SELECT id FROM enrollments 
                WHERE member_id = %s AND status = 'ACTIVE'
                ORDER BY start_date DESC LIMIT 1
                """, (member_id,))
                enrollment = self.cursor.fetchone()

                if not enrollment:
                    # 自动创建注册记录
                    enrollment_id = f"ENR{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
                    insert_enrollment = """
                    INSERT INTO enrollments (id, member_id, plan_id, sponsor_id, start_date, 
                                            relationship_code, status, transaction_type, insurance_line)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    self.cursor.execute(insert_enrollment, (
                        enrollment_id,
                        member_id,
                        'DH-P3678B',  # 默认计划ID
                        'DEFAULTSPO',  # 默认赞助商ID
                        datetime.now().date() - timedelta(days=365),  # 一年前生效
                        '18',  # 本人
                        'ACTIVE',
                        '021',  # 新增
                        'HLT'  # 医疗
                    ))
                    enrollment_id = enrollment_id
                    print(f"为会员 {member_id} 创建默认注册记录: {enrollment_id}")
                else:
                    enrollment_id = enrollment['id']

                # 4. 插入索赔记录
                claim_id = claim_data['claim']['claim_id']
                insert_claim = """
                            INSERT INTO medical_claims (claim_id, member_id, provider_id, enrollment_id, service_date, 
                                                      submission_date, total_billed, status, claim_type, location_type,
                                                      claim_frequency_code, claim_source_code, facility_type_code,
                                                      is_duplicate, fraud_score, notes, procedure_code, procedure_description,
                                                      diagnosis_code)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                self.cursor.execute(insert_claim, (
                    claim_id,
                    member_id,
                    provider_id,
                    enrollment_id,
                    claim_data['claim']['service_date'],
                    claim_data['claim']['submission_date'],
                    claim_data['claim']['billed_amount'],
                    claim_data['claim']['status'],
                    claim_data['claim']['claim_type'],
                    claim_data['claim']['location_type'],
                    claim_data['claim']['claim_frequency_code'],
                    claim_data['claim']['claim_source_code'],
                    claim_data['claim']['facility_type_code'],
                    claim_data['claim']['is_duplicate'],
                    round(random.uniform(0, 30), 2),  # 随机生成欺诈评分
                    "Auto-generated claim",  # 备注
                    claim_data['claim']['procedure_code'],
                    self.map_procedure_code(claim_data['claim']['procedure_code']),
                    current_diagnoses[0]['diagnosis_code'] if current_diagnoses else None
                ))
                print(f"插入索赔记录: {claim_id}")

                # 5. 插入诊断信息 - 使用唯一ID
                for idx,diag in enumerate(claim_data['diagnoses'], 1):
                    # diagnosis_id = f"DIAG{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
                    diagnosis_id = f"DIAG{claim_id}_{idx}"
                    insert_diagnosis = """
                                INSERT INTO diagnoses (diagnosis_id, member_id, provider_id, diagnosis_code, 
                                                    diagnosis_description, onset_date, recorded_date, clinical_status, 
                                                    verification_status, category, severity, notes)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                    self.cursor.execute(insert_diagnosis, (
                        diagnosis_id,
                        member_id,
                        provider_id,
                        diag['diagnosis_code'],
                        diag['diagnosis_description'],
                        diag.get('onset_date'),
                        diag['recorded_date'],
                        diag['clinical_status'],
                        diag['verification_status'],
                        diag.get('category', 'PRIMARY'),
                        diag.get('severity', 'MODERATE'),
                        diag.get('notes', 'Diagnosed during claim processing')
                    ))

                # 6. 插入服务行项目
                for line_num, svc in enumerate(claim_data['service_lines'], 1):
                    # service_line_id = f"SL{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}_{line_num}"
                    service_line_id = f"SL{claim_id}_{line_num}"  # 使用claim_id作为前缀避免冲突
                    insert_service_line = """
                                INSERT INTO claim_service_lines (id, claim_id, line_number, procedure_code, 
                                                              procedure_description, diagnosis_code, service_date, 
                                                              billed_amount, allowed_amount, paid_amount, charge_amount,
                                                              units, modifier_code, place_of_service)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                    self.cursor.execute(insert_service_line, (
                        service_line_id,
                        claim_id,
                        line_num,
                        svc['procedure_code'],
                        svc.get('procedure_description', ''),
                        svc['diagnosis_code'],
                        svc['service_date'],
                        svc['billed_amount'],
                        round(svc['billed_amount'] * random.uniform(0.8, 1.0), 2),  # 允许金额
                        round(svc['billed_amount'] * random.uniform(0.7, 0.9), 2),  # 支付金额
                        svc.get('charge_amount', svc['billed_amount'] * 1.1),  # 收费金额
                        svc['units'],
                        svc.get('modifier_code'),
                        svc.get('place_of_service', '11')
                    ))

                self.conn.commit()
                processed_count += 1
            except Error as e:
                print(f"数据库插入错误: {e}")
                self.conn.rollback()

        # 更新EDI交易状态
        self.update_edi_transaction_status(transaction_id, 'PROCESSED', processed_count)
        print(f"EDI 837文件解析完成，处理了 {processed_count} 条索赔记录")

    def map_facility_type(self, code: str) -> str:
        """映射设施类型代码"""
        facility_map = {
            '11': 'OFFICE',
            '12': 'HOME',
            '21': 'HOSPITAL',
            '22': 'HOSPITAL_OUTPATIENT',
            '23': 'EMERGENCY',
            '24': 'AMBULATORY_SURGERY'
        }
        return facility_map.get(code, 'OFFICE')

    def map_procedure_code(self, code: str) -> str:
        """映射程序代码到描述"""
        procedure_map = {
            '99213': 'Office/outpatient visit est',
            '99214': 'Office/outpatient visit est',
            '99203': 'Office/outpatient visit new',
            '99204': 'Office/outpatient visit new',
            '99215': 'Office/outpatient visit est',
            '99244': 'Office consult'
        }
        return procedure_map.get(code, 'Medical service')

    def parse_edi_835(self, file_path: str):
        """解析EDI 835文件并插入数据库"""
        print(f"开始解析EDI 835文件: {file_path}")
        segments = self.parse_edi_file(file_path)

        # 先记录EDI交易
        transaction_id = self.record_edi_transaction('835', file_path)

        # 解析支付信息
        payments = []
        current_payment = None
        current_claim = None
        current_adjustments = []
        # 在BPR段解析处添加支付方法映射
        payment_method_map = {
            'ACH': 'EFT',
            'CCP': 'CHECK',
            'CTX': 'WIRE',
            'BOP': 'WIRE'
        }

        for segment in segments:
            if segment['segment_id'] == 'BPR':
                # 支付总信息
                current_payment = {
                    'total_amount': float(segment['elements'][1]) if segment['elements'][1] else 0.0,
                    'payment_method': segment['elements'][3],
                    'payment_date': datetime.strptime(segment['elements'][11], '%Y%m%d').date() if len(
                        segment['elements']) > 11 else None,
                    'check_num': segment['elements'][6] if len(segment['elements']) > 6 else None,
                    'claims': []
                }
                payments.append(current_payment)  # 将当前支付添加到payments列表
            elif segment['segment_id'] == 'CLP' and current_payment:
                # 索赔支付信息
                claim_id = segment['elements'][0]
                current_claim = {
                    'claim_id': claim_id,
                    'status': self.map_claim_status(segment['elements'][1]),
                    'billed_amount': float(segment['elements'][2]) if segment['elements'][2] else 0.0,
                    'paid_amount': float(segment['elements'][3]) if segment['elements'][3] else 0.0,
                    'patient_responsibility': float(segment['elements'][4]) if segment['elements'][4] else 0.0,
                    'service_lines': [],
                    'adjustments': []
                }
                current_payment['claims'].append(current_claim)
            elif segment['segment_id'] == 'CAS' and current_claim:
                # 调整信息

                current_claim['adjustments'].append({
                    'adjust_code': segment['elements'][0],
                    'reason_code': segment['elements'][1],
                    'amount': float(segment['elements'][2]) if segment['elements'][2] else 0.0
                })

            elif segment['segment_id'] == 'SVC' and current_claim:
                # 服务行支付详情
                procedure_code = segment['elements'][0][3:] if segment['elements'][0].startswith('HC:') else \
                    segment['elements'][0]
                current_claim['service_lines'].append({
                    'procedure_code': procedure_code,
                    'billed_amount': float(segment['elements'][1]) if segment['elements'][1] else 0.0,
                    'paid_amount': float(segment['elements'][2]) if segment['elements'][2] else 0.0,
                    'allowed_amount': float(segment['elements'][3]) if segment['elements'][3] else 0.0
                })
            elif segment['segment_id'] == 'DTM' and current_claim and segment['elements'][0] == '405':
                # 裁决日期
                adjudication_date = datetime.strptime(segment['elements'][2], '%Y%m%d').date() if segment['elements'][
                                                                                                      1] == 'D8' else None
                current_claim['adjudication_date'] = adjudication_date

        # 插入数据库
        processed_count = 0
        for payment in payments:
            try:
                # 1. 处理每个索赔的支付信息
                for claim in payment['claims']:
                    claim_id = claim['claim_id']
                    processed_count += 1
                    # 检查索赔是否存在
                    self.cursor.execute("SELECT member_id, provider_id FROM medical_claims WHERE claim_id = %s",
                                        (claim_id,))
                    claim_record = self.cursor.fetchone()

                    if not claim_record:
                        print(f"索赔 {claim_id} 不存在，跳过此支付记录")
                        continue

                    member_id = claim_record['member_id']
                    provider_id = claim_record['provider_id']

                    # 更新索赔状态
                    update_claim = """
                    UPDATE medical_claims 
                    SET status = %s, adjudication_date = %s, total_paid = %s, total_allowed = %s
                    WHERE claim_id = %s
                    """
                    self.cursor.execute(update_claim, (
                        claim['status'],
                        claim.get('adjudication_date'),
                        claim['paid_amount'],
                        claim['paid_amount'],  # 简化处理，假设允许金额等于支付金额
                        claim_id
                    ))

                    # 2. 插入支付记录
                    adjustment_details = {
                        'adjustments': claim['adjustments'],
                        'service_line_adjustments': [
                            {
                                'procedure_code': svc['procedure_code'],
                                'paid_amount': svc['paid_amount'],
                                'allowed_amount': svc['allowed_amount']
                            } for svc in claim['service_lines']
                        ]
                    }
                    payment_method = payment_method_map.get(payment['payment_method'], 'CHECK')

                    # 构建汇款通知
                    remittance_advice = f"Payment for claim {claim_id}\n" + \
                                        f"Billed: {claim['billed_amount']}\n" + \
                                        f"Paid: {claim['paid_amount']}\n" + \
                                        f"Patient Responsibility: {claim['patient_responsibility']}"
                    # payment_id = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    payment_id = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
                    insert_payment = """
                    INSERT INTO payments (payment_id, claim_id, payer_id, payee_id, payment_method, 
                        payment_amount, payment_date, transaction_reference, status,
                        adjustment_details, remittance_advice)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    self.cursor.execute(insert_payment, (
                        payment_id,
                        claim_id,
                        'PAYER001',
                        provider_id,
                        payment_method,
                        claim['paid_amount'],
                        payment['payment_date'],
                        payment['check_num'],
                        'COMPLETED',
                        json.dumps(adjustment_details),
                        remittance_advice
                    ))

                    # 3. 插入裁决记录
                    decision = 'APPROVED' if claim['paid_amount'] > 0 else 'DENIED'
                    denial_reason = None
                    adjustment_reason = None

                    if claim['adjustments']:
                        adjustment_reason = "; ".join(
                            f"{adj['adjust_code']}-{adj['reason_code']}"
                            for adj in claim['adjustments']
                        )

                    if decision == 'DENIED':
                        denial_reason = adjustment_reason or "CO-96"  # 默认拒绝原因代码

                    system_rules = {
                        'rules_applied': [
                            {
                                'rule_id': 'AUTO_ADJUSTMENT',
                                'description': 'Automatic claim adjustment based on provider contract'
                            }
                        ]
                    }

                    notes = f"Automatically adjudicated claim {claim_id}. " + \
                            f"Decision: {decision}. " + \
                            f"Billed: {claim['billed_amount']}, Paid: {claim['paid_amount']}"

                    # adjudication_id = f"ADJ{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    adjudication_id = f"ADJ{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
                    decision = 'APPROVED' if claim['paid_amount'] > 0 else 'DENIED'
                    insert_adjudication = """
                        INSERT INTO claim_adjudications (id, claim_id, adjudicator_id, decision, decision_date,
                                                       denial_reason, adjustment_reason, notes, system_rules_used)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                    self.cursor.execute(insert_adjudication, (
                        adjudication_id,
                        claim_id,
                        'SYSTEM',
                        decision,
                        datetime.now(),
                        denial_reason,
                        adjustment_reason,
                        notes,
                        json.dumps(system_rules)
                    ))

                    # 4. 处理调整信息
                    for adj in claim['adjustments']:
                        update_adjudication = """
                        UPDATE claim_adjudications 
                        SET adjustment_reason = %s, denial_reason = %s
                        WHERE id = %s
                        """
                        self.cursor.execute(update_adjudication, (
                            adj['reason_code'],
                            adj['reason_code'] if decision == 'DENIED' else None,
                            adjudication_id
                        ))

                    # 5. 更新服务行支付信息
                    for svc in claim['service_lines']:
                        update_service_line = """
                        UPDATE claim_service_lines 
                        SET paid_amount = %s, allowed_amount = %s
                        WHERE claim_id = %s AND procedure_code = %s
                        """
                        self.cursor.execute(update_service_line, (
                            svc['paid_amount'],
                            svc['allowed_amount'],
                            claim_id,
                            svc['procedure_code']
                        ))

                    # 6. 插入费用分摊记录
                    if claim['patient_responsibility'] > 0:
                        sharing_types = []
                        if claim['patient_responsibility'] > 0:
                            sharing_types.append(f"copay ${claim['patient_responsibility']}")

                        description = f"Patient responsibility for claim {claim_id}: " + \
                                      ", ".join(sharing_types)

                        # sharing_id = f"CS{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        sharing_id = f"CS{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
                        insert_sharing = """
                                INSERT INTO cost_sharing (sharing_id, claim_id, member_id, share_type, 
                                                       applied_amount, remaining_amount, benefit_year, applied_date,
                                                       description)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                        self.cursor.execute(insert_sharing, (
                            sharing_id,
                            claim_id,
                            member_id,
                            'COPAY',
                            claim['patient_responsibility'],
                            0,
                            datetime.now().year,
                            payment['payment_date'],
                            description
                        ))


                self.conn.commit()
            except Error as e:
                print(f"数据库插入错误: {e}")
                self.conn.rollback()

        # 更新EDI交易状态
        self.update_edi_transaction_status(transaction_id, 'PROCESSED', processed_count)
        print(f"EDI 835文件解析完成，处理了 {processed_count} 条支付记录")

    def map_claim_status(self, status_code: str) -> str:
        """映射索赔状态代码"""
        status_map = {
            '1': 'PAID',
            '2': 'PAID',
            '3': 'DENIED',
            '4': 'DENIED',
            '19': 'PAID',
            '20': 'DENIED',
            '21': 'PAID',
            '22': 'DENIED',
            'A': 'PAID',
            'B': 'DENIED',
            'C': 'PAID'
        }
        return status_map.get(status_code, 'RECEIVED')

    def record_edi_transaction(self, transaction_type: str, file_path: str) -> str:
        """记录EDI交易到数据库"""
        # transaction_id = f"EDI{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transaction_id = f"EDI{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        insert_transaction = """
        INSERT INTO edi_transactions (id, transaction_type, original_filename, sender_id, 
                                    receiver_id, transaction_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_transaction, (
            transaction_id,
            transaction_type,
            file_path,
            'SENDERID',
            'RECEIVERID',
            datetime.now(),
            'RECEIVED'
        ))
        self.conn.commit()
        return transaction_id

    def update_edi_transaction_status(self, transaction_id: str, status: str, record_count: int = 0):
        """更新EDI交易状态"""
        update_transaction = """
        UPDATE edi_transactions 
        SET status = %s, record_count = %s, processed_at = NOW()
        WHERE id = %s
        """
        self.cursor.execute(update_transaction, (status, record_count, transaction_id))
        self.conn.commit()


def main():
    parser = EDIParser()
    try:
        parser.connect_db()

        # 解析EDI文件
        from config.config import SAMPLES_DIR
        parser.parse_edi_834(os.path.join(SAMPLES_DIR, 'edi_834_large_sample.txt'))
        parser.parse_edi_837(os.path.join(SAMPLES_DIR, 'edi_837_large_sample.txt'))
        parser.parse_edi_835(os.path.join(SAMPLES_DIR, 'edi_835_large_sample.txt'))

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        parser.close_db()


if __name__ == '__main__':
    main()
