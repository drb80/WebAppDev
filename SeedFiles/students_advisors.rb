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
