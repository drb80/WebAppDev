# This file should contain all the record creation needed to seed the database with its default values.
# The data can then be loaded with the bin/rails db:seed command (or created alongside the database with db:setup).
#
# Examples:
#
#   movies = Movie.create([{ name: "Star Wars" }, { name: "Lord of the Rings" }])
#   Character.create(name: "Luke", movie: movies.first)

Item.destroy_all
50.times do
    Item.create!(what: Faker::Lorem.sentence,
        when: Faker::Date.between(from: Date.today, to: 1.year.from_now))
end
p "Created 50 items"
