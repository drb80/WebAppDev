require "application_system_test_case"

class ItemsTest < ApplicationSystemTestCase
  test "index lists the items" do
    visit items_url

    assert_selector "h1", text: "Items"
    assert_text "Buy milk"
    assert_selector "article", count: 2
  end

  test "creating an item without leaving the page" do
    visit items_url

    within "#item_form" do
      fill_in "What", with: "Walk the dog"
      fill_in "When", with: Date.new(2026, 11, 6)
      click_on "Create"
    end

    within "#items" do
      assert_text "Walk the dog"
    end
    assert_current_path items_path
  end

  test "a blank item shows an error" do
    visit items_url

    within "#item_form" do
      click_on "Create"
    end

    assert_text "What can't be blank"
    assert_selector "article", count: 2
  end

  test "editing an item in place" do
    visit items_url

    within "#item_#{items(:milk).id}" do
      click_on "Edit"
      fill_in "What", with: "Buy oat milk"
      click_on "Update"
    end

    assert_text "Buy oat milk"
    assert_no_text "Buy milk"
  end

  test "deleting an item asks first" do
    visit items_url

    within "#item_#{items(:milk).id}" do
      accept_confirm "Are you sure?" do
        click_on "Delete"
      end
    end

    assert_no_text "Buy milk"
    assert_selector "article", count: 1
  end

  test "a blank update shows an error and can be fixed" do
    visit items_url

    within "#item_#{items(:milk).id}" do
      click_on "Edit"
      fill_in "What", with: ""
      click_on "Update"
      assert_text "What can't be blank"

      fill_in "What", with: "Buy oat milk"
      click_on "Update"
    end

    assert_text "Buy oat milk"
    assert_no_text "can't be blank"
  end
end
