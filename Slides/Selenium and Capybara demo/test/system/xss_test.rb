require "application_system_test_case"

class XssTest < ApplicationSystemTestCase
  test "user input is escaped, not run" do
    visit items_url

    within "#item_form" do
      fill_in "What", with: "<script>alert(1)</script>"
      click_on "Create"
    end

    assert_text "<script>alert(1)</script>"
  end
end
