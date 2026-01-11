from playwright.sync_api import sync_playwright, expect
from contextlib import contextmanager

from sqlalchemy import text
from db.get_cursor import get_cursor 
from .my_numbers import numbers

# For every contact in contacts fill the search_bar with the contact and select 
# the element with title that starts with contact. 
# Doesnt work if contact is start of different contact ( like Joe123, Joe1234 result is ambigous)
def select_contacts_group(search_bar, contacts, page):
  for contact in contacts:
      search_bar.fill(contact)
      try:
        page.click(f'span[ title^="{contact}" ]', timeout=6000)
      except Exception as e:
        print(f"{contact} failed with {str(e)}")
        


@contextmanager
def playwright_page_context():
    """
    Full Playwright lifecycle wrapper.
    - Launches persistent Firefox context
    - Creates a page
    - Yields the page
    - Waits for user input before closing
    """
    
    profile_path = str(" /home/ruz/snap/firefox/common/.mozilla/firefox/playwright")

    
    with sync_playwright() as p:
        browser = p.firefox.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False
        )
        page = browser.new_page()

        try:
            yield page
            
        except Exception as e:
            print(str(e))
            
        finally:
            print("Press Enter to close.")
            input()
            browser.close()


def start_create_group(page):
    """
    Entry point for group creation.
    Clicks:
      New chat → New group
    Ensures search bar is visible before proceeding.
    """
    page.locator('span[data-icon="new-chat-outline"]').click()
    page.locator('span[data-icon="new-group-refreshed-filled"]').click()

    search_bar = page.locator('input[type="text"]')
    expect(search_bar).to_be_visible()

    return search_bar


def format_number_title(num: str) -> str:
    """
    Converts raw number into the WhatsApp-rendered title format.
    This format appears as the 'title' attribute in the DOM.
    """
    return f"+972 5{num[4]}-{num[5:8]}-{num[8:]}"


def select_numbers_group(cur, group_name, page, search_bar, numbers):
    """
    Iterates through numbers and selects each entry.

    There are 3 possible UI scenarios:
    1. Contact without profile picture (span[data-icon])
    2. Contact with profile picture (img[src*='whatsapp.net'])
    3. No contact exists → title equals formatted phone number

    For cases 1 & 2:
      - Exactly ONE element must match selector

    For case 3:
      - The same title may appear twice (main + footer),
        so we allow TWO title matches
    """
    for num in numbers:
        
        num_format = format_number_title(num)
        
        search_bar.fill(num)
        input("stop")

        try:
            selector = (
                "div[role='listitem'] span[data-icon='default-contact-refreshed'], "
                "div[role='listitem'] img[src*='whatsapp.net'], "
                f"span[title='{num_format}']"
            )

            page.wait_for_function(
                f"""
                () => (
                    document.querySelectorAll("{selector}").length === 1 ||
                    document.querySelectorAll("span[title='{num_format}']").length === 2
                )
                """,
                timeout=6000
            )

            entry = page.locator(selector).first
            entry.click(timeout=6000)
            
            set_number(cur, group_name, num, True)

        except Exception as e:
            
            set_number(cur, group_name, num, False)
            print(f"{num} failed with {str(e)}")


def fill_group_name(page, group_name: str):
    """
    Fills WhatsApp group name.

    WhatsApp does NOT use a real <input>.
    Instead, it uses a fake textbox (paragraph + spans).

    Strategy:
    - Locate the two role='textbox' elements
    - Use the FIRST one
    - Click and ensure focus
    - Type using native keyboard input
    """
    fake_input_selector = "div[role='textbox']"
    fake_input_locator = page.locator(fake_input_selector)

    expect(fake_input_locator).to_have_count(2)

    fake_input = fake_input_locator.first
    fake_input.click()
    expect(fake_input).to_be_focused()

    page.keyboard.type(group_name, delay=30)


def confirm_group_creation(page):
    """
    Final confirmation button (checkmark).
    """
    page.locator('span[data-icon="checkmark-medium"]').click()

    
    
    

def get_numbers(cur, group_name):
    result = cur.execute(
        text(
            "SELECT participant "
            "FROM manual_create_group "
            "WHERE group_name = :group_name"
        ),
        {"group_name": group_name}
    )
    return [row[0] for row in result.fetchall()]


def set_number(cur, group_name, number, result: bool):
    cur.execute(
        text(
            "UPDATE manual_create_group "
            "SET success = :success "
            "WHERE group_name = :group_name "
            "AND participant = :participant"
        ),
        {
            "success": result,
            "group_name": group_name,
            "participant": number
        }
    )
    
    
def main():
    
    with get_cursor() as cur:
        with playwright_page_context() as page:
                    
            
            url = "https://web.whatsapp.com"  # site to open
            group_name = "hola"
            numbers = get_numbers(cur, group_name)
            
            page.goto(url)
            
            search_bar = start_create_group(page)
            select_numbers_group(cur, group_name, page, search_bar, numbers)

            # Language-specific selector (temporary solution as noted)
            page.locator("div[aria-label='הבא']").click()

            fill_group_name(page, group_name=group_name)
            confirm_group_creation(page)
            
if __name__ == "__main__":
    main()
    