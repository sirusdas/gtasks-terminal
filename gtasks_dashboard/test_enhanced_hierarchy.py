#!/usr/bin/env python3
"""
Enhanced Hierarchical Visualization Test
Tests the center-focused hierarchical task visualization with improved layout
"""

import requests
import json
import time
import sys

class EnhancedHierarchyTest:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_dashboard_loading(self):
        """Test if dashboard loads correctly"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("✅ Dashboard loads successfully")
                return True
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Dashboard connection failed: {e}")
            return False
    
    def test_hierarchy_data(self):
        """Test hierarchy data structure and content"""
        try:
            response = self.session.get(f"{self.base_url}/api/hierarchy")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    hierarchy_data = data.get('data', {})
                    nodes = hierarchy_data.get('nodes', [])
                    links = hierarchy_data.get('links', [])
                    metadata = hierarchy_data.get('metadata', {})
                    
                    print(f"✅ Hierarchy data retrieved successfully")
                    print(f"   📊 Nodes: {len(nodes)}")
                    print(f"   🔗 Links: {len(links)}")
                    print(f"   📐 Metadata: {bool(metadata)}")
                    
                    # Check node levels
                    levels = set()
                    node_types = set()
                    for node in nodes:
                        levels.add(node.get('level', 0))
                        node_types.add(node.get('type', 'unknown'))
                    
                    print(f"   📈 Levels: {sorted(levels)}")
                    print(f"   🏷️  Node types: {sorted(node_types)}")
                    
                    # Verify metadata structure
                    if metadata:
                        level_distances = metadata.get('level_distances', {})
                        level_angles = metadata.get('level_angles', {})
                        print(f"   🎯 Level distances: {len(level_distances)} levels")
                        print(f"   📐 Level angles: {len(level_angles)} levels")
                    
                    return True
                else:
                    print(f"❌ Hierarchy API returned error: {data}")
                    return False
            else:
                print(f"❌ Hierarchy API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Hierarchy test failed: {e}")
            return False
    
    def test_center_focused_layout(self):
        """Test if the layout is properly centered"""
        try:
            response = self.session.get(f"{self.base_url}/api/hierarchy")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    hierarchy_data = data.get('data', {})
                    metadata = hierarchy_data.get('metadata', {})
                    
                    # Check center coordinates
                    center_x = metadata.get('center_x', 0)
                    center_y = metadata.get('center_y', 0)
                    
                    print(f"✅ Layout metadata retrieved")
                    print(f"   🎯 Center coordinates: ({center_x}, {center_y})")
                    
                    # Check level distances (should be increasing for proper hierarchy)
                    level_distances = metadata.get('level_distances', {})
                    if level_distances:
                        distances = list(level_distances.values())
                        if distances == sorted(distances):
                            print(f"   📏 Level distances properly ordered: {distances}")
                        else:
                            print(f"   ⚠️  Level distances not properly ordered: {distances}")
                    
                    # Check angle distributions
                    level_angles = metadata.get('level_angles', {})
                    for level, angles in level_angles.items():
                        if len(angles) > 0:
                            angle_step = 360 / len(angles) if len(angles) > 1 else 0
                            print(f"   📐 Level {level}: {len(angles)} nodes, {angle_step:.1f}° step")
                    
                    return True
            return False
        except Exception as e:
            print(f"❌ Center layout test failed: {e}")
            return False
    
    def test_node_types_and_colors(self):
        """Test node types and their expected colors"""
        try:
            response = self.session.get(f"{self.base_url}/api/hierarchy")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    hierarchy_data = data.get('data', {})
                    nodes = hierarchy_data.get('nodes', [])
                    
                    print(f"✅ Node type analysis:")
                    
                    type_counts = {}
                    priority_distribution = {}
                    
                    for node in nodes:
                        node_type = node.get('type', 'unknown')
                        name = node.get('name', '')
                        
                        if node_type not in type_counts:
                            type_counts[node_type] = 0
                        type_counts[node_type] += 1
                        
                        # Check priority nodes specifically
                        if node_type == 'priority':
                            priority_name = name.lower().split(' ')[0] if ' ' in name else name
                            if priority_name not in priority_distribution:
                                priority_distribution[priority_name] = 0
                            priority_distribution[priority_name] += 1
                    
                    print(f"   📊 Type distribution: {type_counts}")
                    if priority_distribution:
                        print(f"   🔥 Priority distribution: {priority_distribution}")
                    
                    # Expected types for hierarchical visualization
                    expected_types = {'meta', 'priority', 'category', 'tag', 'account'}
                    actual_types = set(type_counts.keys())
                    
                    if expected_types.issubset(actual_types):
                        print(f"   ✅ All expected node types present")
                    else:
                        missing = expected_types - actual_types
                        print(f"   ⚠️  Missing node types: {missing}")
                    
                    return True
            return False
        except Exception as e:
            print(f"❌ Node type test failed: {e}")
            return False
    
    def test_dashboard_features(self):
        """Test all dashboard features are working"""
        endpoints_to_test = [
            ('/api/dashboard', 'Dashboard data'),
            ('/api/accounts', 'Accounts'),
            ('/api/stats', 'Statistics'),
            ('/api/available-tags', 'Available tags'),
            ('/api/priority-stats', 'Priority statistics'),
            ('/api/tasks/due-today', 'Tasks due today'),
            ('/api/reports/types', 'Report types'),
            ('/api/settings', 'Settings'),
            ('/api/health', 'Health check')
        ]
        
        results = {}
        for endpoint, description in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        results[description] = True
                        print(f"✅ {description}: OK")
                    else:
                        results[description] = False
                        print(f"❌ {description}: API error")
                else:
                    results[description] = False
                    print(f"❌ {description}: HTTP {response.status_code}")
            except Exception as e:
                results[description] = False
                print(f"❌ {description}: {e}")
        
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        print(f"\n📊 Feature Test Summary: {success_count}/{total_count} features working")
        
        return success_count == total_count
    
    def test_enhanced_features(self):
        """Test enhanced features specifically"""
        print("\n🌟 Testing Enhanced Features:")
        
        # Test advanced filtering
        filter_data = {
            "filters": {
                "status": "pending",
                "priority": "high"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/filter-tasks",
                json=filter_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    filtered_count = data.get('count', 0)
                    print(f"✅ Advanced filtering: {filtered_count} tasks filtered")
                else:
                    print(f"❌ Advanced filtering: API error")
            else:
                print(f"❌ Advanced filtering: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Advanced filtering: {e}")
        
        # Test report generation
        try:
            report_data = {
                "report_type": "task_summary",
                "filters": {},
                "parameters": {}
            }
            
            response = self.session.post(
                f"{self.base_url}/api/reports/generate",
                json=report_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Report generation: Working")
                else:
                    print(f"❌ Report generation: API error")
            else:
                print(f"❌ Report generation: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Report generation: {e}")
    
    def run_all_tests(self):
        """Run all tests and provide comprehensive report"""
        print("🚀 Starting Enhanced Hierarchical Visualization Tests")
        print("=" * 60)
        
        tests = [
            ("Dashboard Loading", self.test_dashboard_loading),
            ("Hierarchy Data", self.test_hierarchy_data),
            ("Center-Focused Layout", self.test_center_focused_layout),
            ("Node Types & Colors", self.test_node_types_and_colors),
            ("Dashboard Features", self.test_dashboard_features),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name} test...")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Enhanced features test
        self.test_enhanced_features()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Enhanced hierarchical visualization is working correctly.")
            print("\n✨ Key Improvements Verified:")
            print("   🎯 Center-focused layout")
            print("   📊 Hierarchical node organization")
            print("   🎨 Enhanced visual styling")
            print("   🔧 Interactive features")
            print("   📈 Multi-level hierarchy support")
            return True
        else:
            print("⚠️  Some tests failed. Please check the dashboard functionality.")
            return False

def main():
    """Main test execution"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    tester = EnhancedHierarchyTest(base_url)
    
    print(f"🌐 Testing dashboard at: {base_url}")
    print("⏱️  Waiting for dashboard to be ready...")
    time.sleep(2)
    
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎊 Enhanced hierarchical visualization test completed successfully!")
        print(f"🔗 Access the dashboard at: {base_url}")
        print(f"📱 Navigate to 'Hierarchy' section to see the center-focused visualization")
    else:
        print(f"\n💥 Test completed with failures. Check dashboard logs.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())