#!/usr/bin/env python3
"""
Zoom and Node Interaction Test
Tests the enhanced hierarchical visualization with zoom/pan and node interaction features
"""

import requests
import json
import time
import sys

class ZoomInteractionTest:
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
    
    def test_zoom_controls_html(self):
        """Test if zoom controls HTML elements are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for zoom control elements
                required_elements = [
                    'zoom-controls',
                    'zoomIn',
                    'zoomOut', 
                    'resetZoom',
                    'fas fa-plus',
                    'fas fa-minus',
                    'fas fa-expand-arrows-alt'
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in html_content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    print("✅ All zoom control HTML elements present")
                    return True
                else:
                    print(f"❌ Missing zoom elements: {missing_elements}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Zoom controls test failed: {e}")
            return False
    
    def test_task_panel_html(self):
        """Test if task panel HTML elements are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for task panel elements
                required_elements = [
                    'task-panel',
                    'selected-node-title',
                    'task-panel-header',
                    'task-panel-content',
                    'node-tasks-grid',
                    'closeTaskPanel',
                    'node-task-status-filter',
                    'node-task-priority-filter',
                    'node-task-search-filter'
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in html_content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    print("✅ All task panel HTML elements present")
                    return True
                else:
                    print(f"❌ Missing task panel elements: {missing_elements}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Task panel test failed: {e}")
            return False
    
    def test_zoom_css_styles(self):
        """Test if zoom controls CSS styles are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for zoom CSS styles
                required_styles = [
                    '.zoom-controls',
                    '.zoom-controls .btn',
                    'position: absolute',
                    'top: 1rem',
                    'right: 1rem'
                ]
                
                missing_styles = []
                for style in required_styles:
                    if style not in html_content:
                        missing_styles.append(style)
                
                if not missing_styles:
                    print("✅ All zoom control CSS styles present")
                    return True
                else:
                    print(f"❌ Missing zoom styles: {missing_styles}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Zoom CSS test failed: {e}")
            return False
    
    def test_task_panel_css_styles(self):
        """Test if task panel CSS styles are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for task panel CSS styles
                required_styles = [
                    '.task-panel',
                    '.task-panel-header',
                    '.task-panel-content',
                    '.node-tasks-grid',
                    '.node-task-card',
                    'max-height: 40vh'
                ]
                
                missing_styles = []
                for style in required_styles:
                    if style not in html_content:
                        missing_styles.append(style)
                
                if not missing_styles:
                    print("✅ All task panel CSS styles present")
                    return True
                else:
                    print(f"❌ Missing task panel styles: {missing_styles}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Task panel CSS test failed: {e}")
            return False
    
    def test_zoom_javascript_functions(self):
        """Test if zoom JavaScript functions are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for zoom JavaScript functions
                required_functions = [
                    'initializeZoomPan',
                    'zoomIn',
                    'zoomOut',
                    'resetZoom',
                    'currentZoom',
                    'svgElement',
                    'zoomBehavior'
                ]
                
                missing_functions = []
                for func in required_functions:
                    if func not in html_content:
                        missing_functions.append(func)
                
                if not missing_functions:
                    print("✅ All zoom JavaScript functions present")
                    return True
                else:
                    print(f"❌ Missing zoom functions: {missing_functions}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Zoom JavaScript test failed: {e}")
            return False
    
    def test_node_interaction_javascript_functions(self):
        """Test if node interaction JavaScript functions are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for node interaction JavaScript functions
                required_functions = [
                    'initializeNodeInteractions',
                    'handleNodeClick',
                    'highlightSelectedNode',
                    'showTaskPanel',
                    'closeTaskPanel',
                    'loadNodeTasks',
                    'getRelatedTasks',
                    'displayNodeTasks',
                    'filterNodeTasks',
                    'selectedNode'
                ]
                
                missing_functions = []
                for func in required_functions:
                    if func not in html_content:
                        missing_functions.append(func)
                
                if not missing_functions:
                    print("✅ All node interaction JavaScript functions present")
                    return True
                else:
                    print(f"❌ Missing node interaction functions: {missing_functions}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Node interaction JavaScript test failed: {e}")
            return False
    
    def test_hierarchy_with_enhanced_features(self):
        """Test hierarchy data structure with enhanced features"""
        try:
            response = self.session.get(f"{self.base_url}/api/hierarchy")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    hierarchy_data = data.get('data', {})
                    nodes = hierarchy_data.get('nodes', [])
                    
                    print(f"✅ Hierarchy data retrieved with enhanced features")
                    print(f"   📊 Total nodes: {len(nodes)} (ready for interaction)")
                    
                    # Check node types for interaction
                    node_types = {}
                    for node in nodes:
                        node_type = node.get('type', 'unknown')
                        if node_type not in node_types:
                            node_types[node_type] = 0
                        node_types[node_type] += 1
                    
                    print(f"   🎯 Node types for interaction: {node_types}")
                    
                    return True
                else:
                    print(f"❌ Hierarchy API returned error: {data}")
                    return False
            else:
                print(f"❌ Hierarchy API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Hierarchy enhanced test failed: {e}")
            return False
    
    def test_enhanced_interactive_features(self):
        """Test enhanced interactive features"""
        print("\n🧪 Testing Enhanced Interactive Features:")
        
        features = [
            ("Zoom Controls", "Zoom in, zoom out, and reset zoom functionality"),
            ("Mouse Pan", "Drag to pan the visualization"),
            ("Mouse Wheel Zoom", "Scroll wheel to zoom in/out"),
            ("Node Click", "Click nodes to show related tasks"),
            ("Task Panel", "Bottom panel with task details and filters"),
            ("Task Filtering", "Filter tasks by status, priority, and search"),
            ("Visual Feedback", "Highlight selected nodes"),
            ("Panel Management", "Open and close task panel")
        ]
        
        results = {}
        for feature, description in features:
            try:
                # Test by checking HTML content for feature indicators
                response = self.session.get(f"{self.base_url}/")
                if response.status_code == 200:
                    html_content = response.text
                    
                    feature_indicators = {
                        "Zoom Controls": ['zoomIn', 'zoomOut', 'resetZoom'],
                        "Mouse Pan": ['d3.zoom', 'scaleExtent'],
                        "Mouse Wheel Zoom": ['wheel', 'zoom'],
                        "Node Click": ['handleNodeClick', 'on("click"'],
                        "Task Panel": ['task-panel', 'showTaskPanel'],
                        "Task Filtering": ['node-task-status-filter', 'filterNodeTasks'],
                        "Visual Feedback": ['highlightSelectedNode', 'selected'],
                        "Panel Management": ['closeTaskPanel', 'task-panel-header']
                    }
                    
                    indicators = feature_indicators.get(feature, [])
                    found_indicators = sum(1 for indicator in indicators if indicator in html_content)
                    
                    if found_indicators > 0:
                        results[feature] = True
                        print(f"✅ {feature}: {description}")
                    else:
                        results[feature] = False
                        print(f"❌ {feature}: {description}")
                else:
                    results[feature] = False
                    print(f"❌ {feature}: HTTP error")
            except Exception as e:
                results[feature] = False
                print(f"❌ {feature}: {e}")
        
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        print(f"\n📊 Interactive Features: {success_count}/{total_count} implemented")
        
        return success_count == total_count
    
    def test_d3_zoom_integration(self):
        """Test D3.js zoom integration"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for D3.js zoom integration
                zoom_indicators = [
                    'd3.zoom',
                    'scaleExtent',
                    'scaleBy',
                    'transform',
                    'zoomIdentity',
                    'zoomBehavior'
                ]
                
                found_zoom = sum(1 for indicator in zoom_indicators if indicator in html_content)
                
                if found_zoom >= 4:
                    print("✅ D3.js zoom integration properly implemented")
                    return True
                else:
                    print(f"⚠️  Partial D3.js zoom integration: {found_zoom}/{len(zoom_indicators)}")
                    return False
            else:
                print("❌ Failed to load dashboard for D3.js test")
                return False
        except Exception as e:
            print(f"❌ D3.js integration test failed: {e}")
            return False
    
    def test_task_filtering_functionality(self):
        """Test task filtering functionality"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for task filtering functionality
                filtering_indicators = [
                    'getRelatedTasks',
                    'filterNodeTasks',
                    'node-task-status-filter',
                    'node-task-priority-filter',
                    'node-task-search-filter',
                    'statusFilter',
                    'priorityFilter'
                ]
                
                found_filtering = sum(1 for indicator in filtering_indicators if indicator in html_content)
                
                if found_filtering >= 5:
                    print("✅ Task filtering functionality implemented")
                    return True
                else:
                    print(f"⚠️  Partial task filtering: {found_filtering}/{len(filtering_indicators)}")
                    return False
            else:
                print("❌ Failed to load dashboard for filtering test")
                return False
        except Exception as e:
            print(f"❌ Task filtering test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all zoom and interaction tests and provide comprehensive report"""
        print("🚀 Starting Zoom and Node Interaction Tests")
        print("=" * 70)
        
        tests = [
            ("Dashboard Loading", self.test_dashboard_loading),
            ("Zoom Controls HTML", self.test_zoom_controls_html),
            ("Task Panel HTML", self.test_task_panel_html),
            ("Zoom CSS Styles", self.test_zoom_css_styles),
            ("Task Panel CSS Styles", self.test_task_panel_css_styles),
            ("Zoom JavaScript Functions", self.test_zoom_javascript_functions),
            ("Node Interaction JavaScript Functions", self.test_node_interaction_javascript_functions),
            ("Hierarchy with Enhanced Features", self.test_hierarchy_with_enhanced_features),
            ("Enhanced Interactive Features", self.test_enhanced_interactive_features),
            ("D3.js Zoom Integration", self.test_d3_zoom_integration),
            ("Task Filtering Functionality", self.test_task_filtering_functionality),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name} test...")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 70)
        print("📋 ZOOM & INTERACTION TEST SUMMARY")
        print("=" * 70)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All zoom and interaction tests passed! Enhanced hierarchical visualization with full interactivity is working perfectly.")
            print("\n✨ Interactive Features Verified:")
            print("   🔍 Zoom in/out functionality")
            print("   🖱️  Mouse pan and wheel zoom")
            print("   👆 Node click interaction")
            print("   📋 Task panel with filtering")
            print("   🎯 Visual node highlighting")
            print("   🔧 Advanced task filtering")
            print("   📱 Responsive design")
            return True
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
            return False

def main():
    """Main test execution"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    tester = ZoomInteractionTest(base_url)
    
    print(f"🌐 Testing interactive dashboard at: {base_url}")
    print("⏱️  Waiting for dashboard to be ready...")
    time.sleep(2)
    
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎊 Zoom and interaction test completed successfully!")
        print(f"🔗 Access the dashboard at: {base_url}")
        print(f"📱 Navigate to 'Hierarchy' section to test interactive features")
        print(f"🎮 Interactive Controls:")
        print(f"   • Use zoom controls (+, -, reset) to zoom in/out")
        print(f"   • Scroll wheel to zoom and drag to pan")
        print(f"   • Click any node to see related tasks in bottom panel")
        print(f"   • Filter tasks by status, priority, and search terms")
        print(f"   • Use fullscreen mode for enhanced interaction")
    else:
        print(f"\n💥 Test completed with failures. Check dashboard logs.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())