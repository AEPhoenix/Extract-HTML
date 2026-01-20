import requests
import os
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup


def sanitize_url_for_directory(url):
    """
    Convert a URL into a valid directory name by removing invalid characters.
    """
    # Parse the URL to get the domain and path
    parsed = urlparse(url)
    
    # Combine domain and path, replacing invalid characters
    if parsed.netloc:
        dir_name = parsed.netloc + parsed.path
    else:
        dir_name = parsed.path
    
    # Remove leading/trailing slashes and replace invalid characters
    dir_name = dir_name.strip('/')
    dir_name = re.sub(r'[<>:"|?*]', '_', dir_name)
    dir_name = re.sub(r'[/\\]', '_', dir_name)
    
    # If empty, use a default name
    if not dir_name:
        dir_name = "extracted_page"
    
    return dir_name


def extract_html_from_url(url):
    """
    Extract HTML from a given URL and save it to a directory named after the URL.
    
    Args:
        url (str): The URL to extract HTML from
    
    Returns:
        tuple: (html_file_path, html_content, base_url, dir_name) or (None, None, None, None) on error
    """
    try:
        # Add https:// if no scheme is provided
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"Fetching HTML from: {url}")
        
        # Fetch the HTML content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Create directory name from URL
        dir_name = sanitize_url_for_directory(url)
        
        # Create the directory if it doesn't exist
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"Created directory: {dir_name}")
        
        # Save HTML to file
        html_file_path = os.path.join(dir_name, "index.html")
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"HTML successfully saved to: {html_file_path}")
        return html_file_path, response.text, url, dir_name
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None, None, None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None, None


def extract_linked_styles(html_content, base_url, dir_name):
    """
    Extract linked stylesheets from HTML and download them to the same directory.
    
    Args:
        html_content (str): The HTML content to parse
        base_url (str): The base URL for resolving relative paths
        dir_name (str): The directory where files should be saved
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all stylesheet links
        stylesheet_links = soup.find_all('link', rel='stylesheet')
        
        if not stylesheet_links:
            print("No linked stylesheets found.")
            return True
        
        print(f"\nFound {len(stylesheet_links)} stylesheet(s) to extract...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        downloaded_files = []
        
        for idx, link in enumerate(stylesheet_links, 1):
            href = link.get('href')
            if not href:
                continue
            
            # Resolve relative URLs
            css_url = urljoin(base_url, href)
            
            try:
                print(f"  [{idx}/{len(stylesheet_links)}] Downloading: {css_url}")
                
                # Download the CSS file
                response = requests.get(css_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Generate a safe filename from the URL
                parsed_css_url = urlparse(css_url)
                css_filename = os.path.basename(parsed_css_url.path)
                
                # If no filename, generate one
                if not css_filename or not css_filename.endswith('.css'):
                    css_filename = f"style_{idx}.css"
                
                # Save CSS file
                css_file_path = os.path.join(dir_name, css_filename)
                with open(css_file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # Update the HTML link to point to local file
                link['href'] = css_filename
                
                downloaded_files.append(css_filename)
                print(f"    ✓ Saved to: {css_filename}")
                
            except requests.exceptions.RequestException as e:
                print(f"    ✗ Error downloading {css_url}: {e}")
                continue
            except Exception as e:
                print(f"    ✗ Error processing {css_url}: {e}")
                continue
        
        # Update the HTML file with local references
        html_file_path = os.path.join(dir_name, "index.html")
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"\n✓ Successfully extracted {len(downloaded_files)} stylesheet(s)")
        return True
        
    except Exception as e:
        print(f"Error extracting styles: {e}")
        return False


def main():
    """
    Main function to ask for user input and extract HTML.
    """
    print("HTML Extractor Tool")
    print("=" * 50)
    
    # Ask for user input
    url = input("Enter the URL to extract HTML from: ").strip()
    
    if not url:
        print("Error: URL cannot be empty.")
        return
    
    # Extract HTML
    html_file_path, html_content, base_url, dir_name = extract_html_from_url(url)
    
    if html_file_path:
        print(f"\n✓ Success! HTML file saved at: {html_file_path}")
        
        # Ask if user wants to extract linked styles
        extract_styles = input("\nDo you want to extract linked styles? (y/n): ").strip().lower()
        
        if extract_styles in ['y', 'yes']:
            print("\nExtracting linked stylesheets...")
            extract_linked_styles(html_content, base_url, dir_name)
        else:
            print("Skipping style extraction.")
    else:
        print("\n✗ Failed to extract HTML.")


if __name__ == "__main__":
    main()
