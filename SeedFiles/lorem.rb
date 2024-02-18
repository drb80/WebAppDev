Item.destroy_all
50.times do
    Item.create!(what: Faker::Lorem.sentence,
        when: Faker::Date.between(from: Date.today, to: 1.year.from_now))
end
p "Created 50 items"
