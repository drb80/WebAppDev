# This file should contain all the record creation needed to seed the database with its default values.
# The data can then be loaded with the bin/rails db:seed command (or created alongside the database with db:setup).
#
# Examples:
#
#   movies = Movie.create([{ name: "Star Wars" }, { name: "Lord of the Rings" }])
#   Character.create(name: "Luke", movie: movies.first)
Student.destroy_all
Advisor.destroy_all
5.times {
    advisor = Advisor.create!(
        name: Faker::Name.name,
        email: Faker::Internet.email,
        address: Faker::Address.full_address,
        phone: Faker::PhoneNumber.cell_phone,
    )
    5.times {
        Student.create(
            name: Faker::Name.name,
            email: Faker::Internet.email,
            address: Faker::Address.full_address,
            phone: Faker::PhoneNumber.cell_phone,
            advisor: advisor
        )
    }
}
