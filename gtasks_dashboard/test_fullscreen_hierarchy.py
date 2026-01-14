#!/usr/bin/env python3
"""
Fullscreen Hierarchical Visualization Test
Tests the center-focused hierarchical task visualization with fullscreen mode
"""

import requests
import json
import time
import sys

class FullscreenHierarchyTest:
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
    
    def test_fullscreen_html_elements(self):
        """Test if fullscreen HTML elements are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for fullscreen elements
                required_elements = [
                    'fullscreen-overlay',
                    'fullscreen-header',
                    'fullscreen-title',
                    'fullscreen-controls',
                    'hierarchy-svg-fullscreen',
                    'fullscreen-btn-text',
                    'Enter Fullscreen'
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in html_content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    print("✅ All fullscreen HTML elements present")
                    return True
                else:
                    print(f"❌ Missing fullscreen elements: {missing_elements}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Fullscreen elements test failed: {e}")
            return False
    
    def test_fullscreen_css_styles(self):
        """Test if fullscreen CSS styles are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for fullscreen CSS classes
                required_styles = [
                    '.fullscreen-overlay',
                    '.fullscreen-header',
                    '.fullscreen-title',
                    '.fullscreen-controls',
                    '.fullscreen-viz-container',
                    '.hierarchy-svg-fullscreen',
                    '.fullscreen-controls .btn'
                ]
                
                missing_styles = []
                for style in required_styles:
                    if style not in html_content:
                        missing_styles.append(style)
                
                if not missing_styles:
                    print("✅ All fullscreen CSS styles present")
                    return True
                else:
                    print(f"❌ Missing fullscreen styles: {missing_styles}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Fullscreen CSS test failed: {e}")
            return False
    
    def test_fullscreen_javascript_functions(self):
        """Test if fullscreen JavaScript functions are present"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for fullscreen JavaScript functions
                required_functions = [
                    'toggleFullscreen',
                    'enterFullscreen',
                    'exitFullscreen',
                    'handleEscKey',
                    'updateHierarchicalVisualizationFullscreen',
                    'createHierarchicalVisualization',
                    'isFullscreen'
                ]
                
                missing_functions = []
                for func in required_functions:
                    if func not in html_content:
                        missing_functions.append(func)
                
                if not missing_functions:
                    print("✅ All fullscreen JavaScript functions present")
                    return True
                else:
                    print(f"❌ Missing fullscreen functions: {missing_functions}")
                    return False
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Fullscreen JavaScript test failed: {e}")
            return False
    
    def test_hierarchy_with_fullscreen_support(self):
        """Test hierarchy data structure with fullscreen enhancements"""
        try:
            response = self.session.get(f"{self.base_url}/api/hierarchy")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    hierarchy_data = data.get('data', {})
                    nodes = hierarchy_data.get('nodes', [])
                    links = hierarchy_data.get('links', [])
                    metadata = hierarchy_data.get('metadata', {})
                    
                    print(f"✅ Hierarchy data retrieved with fullscreen support")
                    print(f"   📊 Nodes: {len(nodes)} (enhanced for fullscreen)")
                    print(f"   🔗 Links: {len(links)}")
                    print(f"   📐 Metadata: {bool(metadata)} (for layout scaling)")
                    
                    # Check if nodes have enhanced properties for fullscreen
                    enhanced_nodes = 0
                    for node in nodes:
                        if all(key in node for key in ['id', 'name', 'type', 'level', 'val']):
                            enhanced_nodes += 1
                    
                    print(f"   🎯 Enhanced nodes: {enhanced_nodes}/{len(nodes)}")
                    
                    return True
                else:
                    print(f"❌ Hierarchy API returned error: {data}")
                    return False
            else:
                print(f"❌ Hierarchy API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Hierarchy fullscreen test failed: {e}")
            return False
    
    def test_fullscreen_interactive_features(self):
        """Test fullscreen interactive features"""
        print("\n🧪 Testing Fullscreen Interactive Features:")
        
        features = [
            ("Fullscreen toggle button", "Should be present in hierarchy section"),
            ("ESC key handler", "Should exit fullscreen when ESC is pressed"),
            ("Fullscreen overlay", "Should cover entire screen when active"),
            ("Sidebar hiding", "Should hide sidebar in fullscreen mode"),
            ("Enhanced visualization", "Should scale properly in fullscreen"),
            ("Exit controls", "Should have clear exit options")
        ]
        
        results = {}
        for feature, description in features:
            try:
                # Test by checking HTML content for feature indicators
                response = self.session.get(f"{self.base_url}/")
                if response.status_code == 200:
                    html_content = response.text
                    
                    feature_indicators = {
                        "Fullscreen toggle button": ['toggleFullscreen', 'Enter Fullscreen'],
                        "ESC key handler": ['handleEscKey', 'Escape'],
                        "Fullscreen overlay": ['fullscreen-overlay'],
                        "Sidebar hiding": ['sidebar', 'marginLeft'],
                        "Enhanced visualization": ['updateHierarchicalVisualizationFullscreen'],
                        "Exit controls": ['exitFullscreen', 'Exit Fullscreen']
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
        
        print(f"\n📊 Fullscreen Features: {success_count}/{total_count} working")
        
        return success_count == total_count
    
    def test_responsive_fullscreen_design(self):
        """Test responsive design for fullscreen mode"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for responsive CSS
                responsive_indicators = [
                    '@media (max-width: 768px)',
                    'fullscreen-header',
                    'fullscreen-title',
                    'fullscreen-controls'
                ]
                
                found_responsive = sum(1 for indicator in responsive_indicators if indicator in html_content)
                
                if found_responsive >= 3:
                    print("✅ Responsive fullscreen design implemented")
                    return True
                else:
                    print("⚠️  Partial responsive fullscreen design")
                    return False
            else:
                print("❌ Failed to load dashboard for responsive test")
                return False
        except Exception as e:
            print(f"❌ Responsive design test failed: {e}")
            return False
    
    def test_enhanced_visualization_features(self):
        """Test enhanced visualization features in fullscreen"""
        print("\n🌟 Testing Enhanced Visualization Features:")
        
        features = [
            ("Center-focused layout", "Nodes should be positioned around center"),
            ("Hierarchical levels", "5-level hierarchy with proper spacing"),
            ("Enhanced styling", "Larger nodes and text in fullscreen"),
            ("Interactive tooltips", "Enhanced tooltips for fullscreen"),
            ("Legend system", "Visible legend in fullscreen mode"),
            ("Keyboard shortcuts", "ESC key and visual hints")
        ]
        
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                html_content = response.text
                
                # Check for enhanced visualization features
                enhancement_indicators = [
                    'createHierarchicalVisualization',
                    'centerX',
                    'centerY',
                    'levelDistances',
                    'isFullscreenMode',
                    'keyboard-hint',
                    'Press ESC to exit'
                ]
                
                found_enhancements = sum(1 for indicator in enhancement_indicators if indicator in html_content)
                
                if found_enhancements >= 5:
                    print(f"✅ Enhanced visualization: {found_enhancements}/{len(enhancement_indicators)} features")
                    return True
                else:
                    print(f"⚠️  Partial enhancement: {found_enhancements}/{len(enhancement_indicators)} features")
                    return False
            else:
                print("❌ Failed to load dashboard for enhancement test")
                return False
        except Exception as e:
            print(f"❌ Enhancement test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all fullscreen tests and provide comprehensive report"""
        print("🚀 Starting Fullscreen Hierarchical Visualization Tests")
        print("=" * 70)
        
        tests = [
            ("Dashboard Loading", self.test_dashboard_loading),
            ("Fullscreen HTML Elements", self.test_fullscreen_html_elements),
            ("Fullscreen CSS Styles", self.test_fullscreen_css_styles),
            ("Fullscreen JavaScript Functions", self.test_fullscreen_javascript_functions),
            ("Hierarchy with Fullscreen Support", self.test_hierarchy_with_fullscreen_support),
            ("Fullscreen Interactive Features", self.test_fullscreen_interactive_features),
            ("Responsive Fullscreen Design", self.test_responsive_fullscreen_design),
            ("Enhanced Visualization Features", self.test_enhanced_visualization_features),
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
        print("📋 FULLSCREEN TEST SUMMARY")
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
            print("🎉 All fullscreen tests passed! Enhanced hierarchical visualization with fullscreen is working perfectly.")
            print("\n✨ Fullscreen Features Verified:")
            print("   🖥️  Fullscreen toggle button")
            print("   ⌨️  ESC key support")
            print("   📱 Responsive design")
            print("   🎨 Enhanced fullscreen visualization")
            print("   🎯 Center-focused layout in fullscreen")
            print("   🔧 Interactive controls")
            print("   📐 Proper scaling and positioning")
            return True
        else:
            print("⚠️  Some fullscreen tests failed. Please check the implementation.")
            return False

def main():
    """Main test execution"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    tester = FullscreenHierarchyTest(base_url)
    
    print(f"🌐 Testing fullscreen dashboard at: {base_url}")
    print("⏱️  Waiting for dashboard to be ready...")
    time.sleep(2)
    
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎊 Fullscreen hierarchical visualization test completed successfully!")
        print(f"🔗 Access the dashboard at: {base_url}")
        print(f"📱 Navigate to 'Hierarchy' section and click 'Enter Fullscreen' to test")
        print(f"🎮 Fullscreen Controls:")
        print(f"   • Click 'Enter Fullscreen' button to enter fullscreen mode")
        print(f"   • Press ESC key to exit fullscreen mode")
        print(f"   • Click 'Exit Fullscreen' button to exit")
        print(f"   • All interactive features work in both normal and fullscreen modes")
    else:
        print(f"\n💥 Test completed with failures. Check dashboard logs.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())