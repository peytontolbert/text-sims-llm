from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
from PIL import Image, ImageDraw, ImageFont
import os

class BrowserController:
    def __init__(self, window_width=1000, window_height=1000):
        # Configure Edge WebDriver
        edge_options = Options()
        edge_options.add_argument(f"--window-size={window_width},{window_height}")
        edge_options.add_argument("--use-fake-ui-for-media-stream")  # Auto-allow microphone access
        edge_options.add_argument("--use-fake-device-for-media-stream")  # Enable fake media devices
        
        # Initialize the driver with our audio options
        self.driver = webdriver.Edge(options=edge_options)
        
        # Initialize audio state
        self.virtual_mic = None
        self.audio_initialized = False
        
        # Wait for the browser to open
        time.sleep(2)
        
        # Store both viewport and screenshot dimensions
        self.viewport_width = self.driver.execute_script("return window.innerWidth")
        self.viewport_height = self.driver.execute_script("return window.innerHeight")
        # Calculate the difference between window and viewport size
        width_diff = window_width - self.viewport_width
        height_diff = window_height - self.viewport_height
        
        # Adjust window size to account for the difference
        self.driver.set_window_size(window_width + width_diff, window_height + height_diff)
        
        self.screenshot_width = 1008    
        self.screenshot_height = 1008
        
        self.actions = ActionChains(self.driver)
        self.last_mouse_position = None
        
        print(f"Initialized browser with viewport dimensions: {self.viewport_width}x{self.viewport_height}")

    def initialize_virtual_microphone(self, virtual_mic):
        """Initialize the virtual microphone before navigation"""
        self.virtual_mic = virtual_mic
        
        try:
            # Navigate to a blank page first to set up audio context
            self.driver.get('about:blank')
            
            # Set up initial audio context with virtual microphone
            setup_script = """
            async function initializeAudio() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: false,
                            noiseSuppression: false,
                            autoGainControl: false,
                            deviceId: 'virtual-microphone'
                        }
                    });
                    
                    // Create audio context
                    const audioContext = new (window.AudioContext || window.webkitAudioContext)({
                        sampleRate: arguments[0]
                    });
                    
                    // Create a MediaStreamSource but DON'T connect to destination
                    const source = audioContext.createMediaStreamSource(stream);
                    
                    // Create a GainNode to control volume (set to 0 to prevent feedback)
                    const gainNode = audioContext.createGain();
                    gainNode.gain.value = 0;
                    
                    // Connect source to gain node only - not to destination
                    source.connect(gainNode);
                    
                    // Store the audio context and nodes globally for later use
                    window.virtualMicAudio = {
                        context: audioContext,
                        source: source,
                        gainNode: gainNode
                    };
                    
                    return true;
                } catch (err) {
                    console.error('Error initializing audio:', err);
                    return false;
                }
            }
            return initializeAudio();
            """
            
            # Start the virtual microphone if it's not already running
            if not self.virtual_mic.is_active:
                self.virtual_mic.start()
                
            # Execute the setup script with the virtual mic's sample rate
            result = self.driver.execute_script(setup_script, self.virtual_mic.sample_rate)
            
            if result:
                print("Successfully initialized virtual microphone (output disabled)")
                self.audio_initialized = True
                return True
            else:
                print("Failed to initialize virtual microphone")
                return False
                
        except Exception as e:
            print(f"Error initializing virtual microphone: {e}")
            return False

    def navigate(self, url):
        """Navigate to a specified URL and ensure audio is set up."""
        # Verify virtual microphone is initialized
        if not self.audio_initialized:
            print("Warning: Virtual microphone not initialized before navigation")
            if self.virtual_mic:
                self.initialize_virtual_microphone(self.virtual_mic)
        
        self.driver.get(url)
        print(f"Navigated to {url}")
        
        # Verify audio permissions after navigation
        if self.setup_audio_permissions():
            if self.wait_for_audio_ready():
                print("Audio system successfully initialized")
            else:
                print("Warning: Audio system not ready")
        else:
            print("Warning: Failed to set up audio permissions")
        
        time.sleep(2)  # Wait for the page to load

    def locate_element_by_text(self, text):
        """Locate an element by link text and return its center coordinates."""
        try:
            element = self.driver.find_element(By.LINK_TEXT, text)
            location = element.location
            size = element.size
            # Calculate center coordinates within the browser
            center_x = location['x'] + (size['width'] / 2)
            center_y = location['y'] + (size['height'] / 2)
            print(f"Located element '{text}' at ({center_x}, {center_y})")
            return center_x, center_y
        except Exception as e:
            print(f"Error locating element by text '{text}': {e}")
            return None, None

    def move_mouse_to(self, x, y):
        """Move the virtual mouse to the specified coordinates within the browser."""
        print(f" window dimensions: {self.viewport_width}x{self.viewport_height}")
        print(f" last mouse position: {self.last_mouse_position}")
        if self.last_mouse_position is None:
            # If this is the first movement, set the initial position as the current (0, 0)
            self.last_mouse_position = (0, 0)
        if 0 <= x <= self.viewport_width and 0 <= y <= self.viewport_height:
            # Move to the coordinates within the browser window
            offset_x = x - self.last_mouse_position[0]
            offset_y = y - self.last_mouse_position[1]
            self.actions.move_by_offset(offset_x, offset_y).perform()
            self.last_mouse_position = (x, y)
            self.take_screenshot(f"images/screenshot_{x}_{y}.png")
            print(f"Moved mouse to ({x}, {y}) within the browser window.")
            self.last_mouse_position = (x, y)  # Update mouse position
        else:
            print(f"Coordinates ({x}, {y}) are out of browser bounds.")

    def click_at(self, x, y):
        """Move the virtual mouse to (x, y) and perform a click."""
        self.move_mouse_to(x, y)
        self.actions.click().perform()
        print(f"Clicked at ({x}, {y}) within the browser window.")

    def normalize_coordinates(self, x, y, from_screenshot=True):
        """
        Convert coordinates between screenshot (1000x1000) and viewport spaces.
        
        Args:
            x (float): X coordinate
            y (float): Y coordinate
            from_screenshot (bool): If True, convert from screenshot to viewport.
                                  If False, convert from viewport to screenshot.
        
        Returns:
            tuple: (normalized_x, normalized_y)
        """
        if from_screenshot:
            # Convert from 1000x1000 screenshot space to viewport space
            normalized_x = (x * self.viewport_width) / self.screenshot_width
            normalized_y = (y * self.viewport_height) / self.screenshot_height
            print(f"Converting screenshot ({x}, {y}) -> viewport ({normalized_x}, {normalized_y})")
        else:
            # Convert from viewport space to 1000x1000 screenshot space
            normalized_x = (x * self.screenshot_width) / self.viewport_width
            normalized_y = (y * self.screenshot_height) / self.viewport_height
            print(f"Converting viewport ({x}, {y}) -> screenshot ({normalized_x}, {normalized_y})")
        
        return normalized_x, normalized_y

    def take_screenshot(self, filename="images/screenshot.png"):
        """Take a screenshot and overlay coordinate system scaled to 1000x1000."""
        # Take the screenshot
        self.driver.save_screenshot(filename)
        
        try:
            # Open and resize the screenshot to 1000x1000
            image = Image.open(filename)
            draw = ImageDraw.Draw(image)

            try:
                font = ImageFont.truetype("arial.ttf", 15)
            except IOError:
                font = None
            
            # Overlay the mouse position if available
            if self.last_mouse_position:
                # Draw viewport coordinates in red
                viewport_x, viewport_y = self.last_mouse_position
                mouse_size = 10
                draw.ellipse(
                    (viewport_x - mouse_size, viewport_y - mouse_size, 
                     viewport_x + mouse_size, viewport_y + mouse_size),
                    fill='red',
                    outline='black'
                )
                draw.text((viewport_x + 15, viewport_y), 
                         f"Viewport: ({int(viewport_x)}, {int(viewport_y)})", 
                         fill="red", 
                         font=font)
                
                # Draw screenshot coordinates in blue
                screenshot_x, screenshot_y = self.normalize_coordinates(
                    viewport_x, 
                    viewport_y, 
                    from_screenshot=False
                )
                draw.ellipse(
                    (screenshot_x - mouse_size, screenshot_y - mouse_size, 
                     screenshot_x + mouse_size, screenshot_y + mouse_size),
                    fill='blue',
                    outline='black'
                )
                draw.text((screenshot_x + 15, screenshot_y + 25), 
                         f"Screenshot: ({int(screenshot_x)}, {int(screenshot_y)})", 
                         fill="blue", 
                         font=font)

            image = image.resize((self.screenshot_width, self.screenshot_height))
            # Save the modified screenshot
            image.save(filename)
            print(f"Enhanced screenshot saved with viewport and screenshot coordinates at {filename}")
        except Exception as e:
            print(f"Error processing screenshot: {e}")

    def close(self):
        """Close the browser."""
        self.driver.quit()
        print("Browser closed.")

    def type_text(self, text):
        """Type text into the currently focused element."""
        try:
            actions = ActionChains(self.driver)
            actions.send_keys(text)
            actions.perform()
            print(f"Typed text")
            time.sleep(0.5)  # Small delay after typing
        except Exception as e:
            print(f"Error typing text: {e}")

    def press_key(self, key):
        """Press a specific key (e.g., Enter, Tab, etc.)."""
        try:
            actions = ActionChains(self.driver)
            actions.send_keys(getattr(Keys, key.upper()))
            actions.perform()
            print(f"Pressed key: {key}")
            time.sleep(0.5)  # Small delay after key press
        except Exception as e:
            print(f"Error pressing key: {e}")

    def click_and_type(self, x, y, text):
        """Click at coordinates and type text."""
        self.click_at(x, y)
        time.sleep(0.5)  # Wait for click to register
        self.type_text(text)

    def scroll_down(self, amount=300):
        """
        Scroll the page down by the specified amount of pixels.
        Args:
            amount (int): Number of pixels to scroll down. Default is 300.
        """
        try:
            self.driver.execute_script(f"window.scrollBy(0, {amount});")
            print(f"Scrolled down {amount} pixels")
            time.sleep(0.5)  # Small delay after scrolling
            self.take_screenshot()  # Take a screenshot after scrolling
        except Exception as e:
            print(f"Error scrolling down: {e}")

    def scroll_up(self, amount=300):
        """
        Scroll the page up by the specified amount of pixels.
        Args:
            amount (int): Number of pixels to scroll up. Default is 300.
        """
        try:
            self.driver.execute_script(f"window.scrollBy(0, -{amount});")
            print(f"Scrolled up {amount} pixels")
            time.sleep(0.5)  # Small delay after scrolling
            self.take_screenshot()  # Take a screenshot after scrolling
        except Exception as e:
            print(f"Error scrolling up: {e}")

    def scroll_to_element(self, element_text):
        """
        Scroll to make an element with specific text visible.
        Args:
            element_text (str): The text of the element to scroll to
        """
        try:
            element = self.driver.find_element(By.LINK_TEXT, element_text)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            print(f"Scrolled to element with text: {element_text}")
            time.sleep(0.5)  # Small delay after scrolling
            self.take_screenshot()  # Take a screenshot after scrolling
        except Exception as e:
            print(f"Error scrolling to element: {e}")

    def setup_audio_permissions(self):
        """Set up browser audio permissions and virtual microphone access."""
        try:
            # Execute JavaScript to set up audio context and request microphone access
            setup_script = """
            async function setupAudio() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: false,
                            noiseSuppression: false,
                            autoGainControl: false
                        }
                    });
                    
                    // Create audio context if it doesn't exist
                    if (!window.virtualMicAudio) {
                        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        const source = audioContext.createMediaStreamSource(stream);
                        const gainNode = audioContext.createGain();
                        gainNode.gain.value = 0;
                        
                        // Connect source to gain node only
                        source.connect(gainNode);
                        
                        window.virtualMicAudio = {
                            context: audioContext,
                            source: source,
                            gainNode: gainNode
                        };
                    }
                    
                    return true;
                } catch (err) {
                    console.error('Error setting up audio:', err);
                    return false;
                }
            }
            return setupAudio();
            """
            
            result = self.driver.execute_script(setup_script)
            if result:
                print("Successfully set up browser audio permissions (output disabled)")
                return True
            else:
                print("Failed to set up browser audio")
                return False
                
        except Exception as e:
            print(f"Error setting up browser audio permissions: {e}")
            return False

    def wait_for_audio_ready(self, timeout=10):
        """Wait for audio system to be ready and permissions to be granted."""
        try:
            check_script = """
            return navigator.mediaDevices.getUserMedia({ audio: true })
                .then(() => true)
                .catch(() => false);
            """
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.driver.execute_script(check_script):
                    print("Audio system is ready")
                    return True
                time.sleep(1)
                
            print("Timeout waiting for audio system")
            return False
            
        except Exception as e:
            print(f"Error checking audio status: {e}")
            return False

