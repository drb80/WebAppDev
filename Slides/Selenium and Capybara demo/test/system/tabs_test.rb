require "application_system_test_case"

class TabsTest < ApplicationSystemTestCase
  test "the first tab is selected on the home page" do
    visit root_url

    within "nav.tabs" do
      assert_selector "a[aria-current='page']", text: "Courses"
    end
    assert_text "CS3710"
  end

  test "clicking a tab shows that tab's records" do
    visit root_url

    within("nav.tabs") { click_on "Students" }

    assert_selector "h1", text: "Students"
    assert_text "Lovelace"
    assert_no_text "CS3710"
    assert_current_path students_path
  end

  test "only the clicked tab is selected" do
    visit root_url

    within("nav.tabs") { click_on "Sections" }

    within "nav.tabs" do
      assert_selector "a[aria-current='page']", count: 1
      assert_selector "a[aria-current='page']", text: "Sections"
    end
  end

  test "switching tabs does not reload the page" do
    visit root_url
    # A full page load would wipe out this JavaScript variable
    execute_script "window.stillHere = true"

    within("nav.tabs") { click_on "Students" }
    assert_selector "h1", text: "Students"
    within("nav.tabs") { click_on "Sections" }
    assert_selector "h1", text: "Sections"

    assert_equal true, evaluate_script("window.stillHere")
  end

  test "the Back button returns to the previous tab" do
    visit root_url
    within("nav.tabs") { click_on "Students" }
    assert_selector "h1", text: "Students"

    go_back

    assert_selector "h1", text: "Courses"
    assert_current_path root_path
  end
end
