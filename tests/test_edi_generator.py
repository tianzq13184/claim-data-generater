"""
Tests for EDI data generator
"""

import os
import sys
import unittest
import tempfile
import shutil
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import directly from generator module to avoid parser dependencies
from src.edi import generator
from src.edi.generator import (
    generate_edi_834,
    generate_edi_837,
    generate_edi_835,
    generate_id,
    generate_isa_gs_segments,
    global_data
)


class TestEDIGenerator(unittest.TestCase):
    """Test cases for EDI generator"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test output
        self.test_dir = tempfile.mkdtemp()
        self.test_output_834 = os.path.join(self.test_dir, "test_834.txt")
        self.test_output_837 = os.path.join(self.test_dir, "test_837.txt")
        self.test_output_835 = os.path.join(self.test_dir, "test_835.txt")
        
        # Clear global data
        global_data['members'] = {}
        global_data['providers'] = {}
        global_data['enrollments'] = {}
        global_data['claims'] = {}

    @staticmethod
    def _get_control_from_segment(seg, index):
        """Extract control number from EDI segment at given index.
        
        Handles various formats:
        - Segment with ~ delimiter: 'ISA*...*123~' -> '123'
        - Segment without ~: 'ISA*...*123' -> '123'
        - Segment with whitespace: 'ISA*...*123 ' -> '123'
        
        Args:
            seg: EDI segment line
            index: Index in split('*') array
            
        Returns:
            Cleaned control number string
        """
        return seg.split('*')[index].split('~')[0].strip()

    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_generate_id(self):
        """Test ID generation"""
        id1 = generate_id("TEST", 8)
        id2 = generate_id("TEST", 8)
        
        self.assertTrue(id1.startswith("TEST"))
        self.assertTrue(id2.startswith("TEST"))
        self.assertNotEqual(id1, id2)
        self.assertEqual(len(id1), len("TEST") + 8)
        self.assertEqual(len(id2), len("TEST") + 8)

    def test_isa_gs_segments(self):
        """Test ISA and GS segment generation"""
        current_date = datetime.now()
        
        # Test 834
        segments_834, control_num_834 = generate_isa_gs_segments("834", current_date)
        self.assertEqual(len(segments_834), 2)
        self.assertTrue(segments_834[0].startswith("ISA"))
        self.assertTrue(segments_834[1].startswith("GS"))
        self.assertIn("BE", segments_834[1])
        self.assertIn("004010X095A1", segments_834[1])
        self.assertIsNotNone(control_num_834)
        
        # Test 837
        segments_837, control_num_837 = generate_isa_gs_segments("837", current_date)
        self.assertTrue(segments_837[1].startswith("GS"))
        self.assertIn("HC", segments_837[1])
        self.assertIn("004010X098A1", segments_837[1])
        
        # Test 835
        segments_835, control_num_835 = generate_isa_gs_segments("835", current_date)
        self.assertTrue(segments_835[1].startswith("GS"))
        self.assertIn("HP", segments_835[1])
        self.assertIn("004010X091A1", segments_835[1])

    def test_generate_edi_834(self):
        """Test EDI 834 file generation"""
        num_members = 10
        
        # Generate file
        result = generate_edi_834(num_members, self.test_output_834)
        
        # Check file exists
        self.assertTrue(os.path.exists(self.test_output_834))
        
        # Read and validate file
        with open(self.test_output_834, 'r', encoding='utf8') as f:
            content = f.read()
        
        # Check basic structure
        self.assertIn("ISA", content)
        self.assertIn("GS", content)
        self.assertIn("ST*834", content)
        self.assertIn("SE", content)
        self.assertIn("GE", content)
        self.assertIn("IEA", content)
        
        # Check segment count in SE
        lines = content.split('\n')
        se_line = [line for line in lines if line.startswith("SE")][0]
        se_count = int(se_line.split('*')[1])
        
        # Count segments from ST to SE (inclusive)
        st_index = next(i for i, line in enumerate(lines) if line.startswith("ST"))
        se_index = next(i for i, line in enumerate(lines) if line.startswith("SE"))
        expected_count = se_index - st_index + 1
        
        self.assertEqual(se_count, expected_count, 
                        f"SE count mismatch: expected {expected_count}, got {se_count}")
        
        # Check ISA and IEA control numbers match
        isa_line = [line for line in lines if line.startswith("ISA")][0]
        iea_line = [line for line in lines if line.startswith("IEA")][0]
        isa_control = self._get_control_from_segment(isa_line, 13)
        iea_control = self._get_control_from_segment(iea_line, 2)
        self.assertEqual(isa_control, iea_control, 
                        "ISA and IEA control numbers should match")
        
        # Check version consistency
        gs_line = [line for line in lines if line.startswith("GS")][0]
        st_line = [line for line in lines if line.startswith("ST")][0]
        gs_version = gs_line.split('*')[8]
        st_version = st_line.split('*')[3]
        self.assertEqual(gs_version, st_version, 
                        "GS and ST versions should match for 834")

    def test_generate_edi_837(self):
        """Test EDI 837 file generation"""
        # First generate some members for 837
        generate_edi_834(10, os.path.join(self.test_dir, "temp_834.txt"))
        
        num_claims = 5
        result = generate_edi_837(num_claims, 1, self.test_output_837)
        
        # Check file exists
        self.assertTrue(os.path.exists(self.test_output_837))
        
        # Read and validate file
        with open(self.test_output_837, 'r', encoding='utf8') as f:
            content = f.read()
        
        # Check basic structure
        self.assertIn("ISA", content)
        self.assertIn("GS", content)
        self.assertIn("ST*837", content)
        self.assertIn("BHT", content)
        self.assertIn("CLM", content)
        self.assertIn("SE", content)
        self.assertIn("GE", content)
        self.assertIn("IEA", content)
        
        # Check segment count in SE
        lines = content.split('\n')
        se_line = [line for line in lines if line.startswith("SE")][0]
        se_count = int(se_line.split('*')[1])
        
        st_index = next(i for i, line in enumerate(lines) if line.startswith("ST"))
        se_index = next(i for i, line in enumerate(lines) if line.startswith("SE"))
        expected_count = se_index - st_index + 1
        
        self.assertEqual(se_count, expected_count,
                        f"SE count mismatch: expected {expected_count}, got {se_count}")
        
        # Check ISA and IEA control numbers match
        isa_line = [line for line in lines if line.startswith("ISA")][0]
        iea_line = [line for line in lines if line.startswith("IEA")][0]
        isa_control = self._get_control_from_segment(isa_line, 13)
        iea_control = self._get_control_from_segment(iea_line, 2)
        self.assertEqual(isa_control, iea_control,
                        "ISA and IEA control numbers should match")

    def test_generate_edi_835(self):
        """Test EDI 835 file generation"""
        # First generate members and claims
        generate_edi_834(10, os.path.join(self.test_dir, "temp_834.txt"))
        generate_edi_837(10, 1, os.path.join(self.test_dir, "temp_837.txt"))
        
        num_payments = 5
        result = generate_edi_835(num_payments, self.test_output_835)
        
        # Check file exists
        self.assertTrue(os.path.exists(self.test_output_835))
        
        # Read and validate file
        with open(self.test_output_835, 'r', encoding='utf8') as f:
            content = f.read()
        
        # Check basic structure
        self.assertIn("ISA", content)
        self.assertIn("GS", content)
        self.assertIn("ST*835", content)
        self.assertIn("BPR", content)
        self.assertIn("CLP", content)
        self.assertIn("SE", content)
        self.assertIn("GE", content)
        self.assertIn("IEA", content)
        
        # Check segment count in SE
        lines = content.split('\n')
        se_line = [line for line in lines if line.startswith("SE")][0]
        se_count = int(se_line.split('*')[1])
        
        st_index = next(i for i, line in enumerate(lines) if line.startswith("ST"))
        se_index = next(i for i, line in enumerate(lines) if line.startswith("SE"))
        expected_count = se_index - st_index + 1
        
        self.assertEqual(se_count, expected_count,
                        f"SE count mismatch: expected {expected_count}, got {se_count}")
        
        # Check ISA and IEA control numbers match
        isa_line = [line for line in lines if line.startswith("ISA")][0]
        iea_line = [line for line in lines if line.startswith("IEA")][0]
        isa_control = self._get_control_from_segment(isa_line, 13)
        iea_control = self._get_control_from_segment(iea_line, 2)
        self.assertEqual(isa_control, iea_control,
                        "ISA and IEA control numbers should match")

    def test_edi_834_segment_structure(self):
        """Test EDI 834 segment structure and required segments"""
        generate_edi_834(5, self.test_output_834)
        
        with open(self.test_output_834, 'r', encoding='utf8') as f:
            content = f.read()
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Check required segments exist
        segment_ids = [line.split('*')[0] for line in lines]
        
        self.assertIn("ISA", segment_ids)
        self.assertIn("GS", segment_ids)
        self.assertIn("ST", segment_ids)
        self.assertIn("BGN", segment_ids)
        self.assertIn("INS", segment_ids)
        self.assertIn("NM1", segment_ids)
        self.assertIn("DMG", segment_ids)
        self.assertIn("SE", segment_ids)
        self.assertIn("GE", segment_ids)
        self.assertIn("IEA", segment_ids)

    def test_edi_837_segment_structure(self):
        """Test EDI 837 segment structure"""
        generate_edi_834(5, os.path.join(self.test_dir, "temp_834.txt"))
        generate_edi_837(3, 1, self.test_output_837)
        
        with open(self.test_output_837, 'r', encoding='utf8') as f:
            content = f.read()
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        segment_ids = [line.split('*')[0] for line in lines]
        
        # Check required segments
        self.assertIn("ISA", segment_ids)
        self.assertIn("GS", segment_ids)
        self.assertIn("ST", segment_ids)
        self.assertIn("BHT", segment_ids)
        self.assertIn("HL", segment_ids)
        self.assertIn("CLM", segment_ids)
        self.assertIn("SE", segment_ids)
        self.assertIn("GE", segment_ids)
        self.assertIn("IEA", segment_ids)


if __name__ == '__main__':
    unittest.main()

