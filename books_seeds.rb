#            111 11111
# 0123 567 9 123 56789
# ISBN 978-0-306-40615

Ones = [5, 7, 11, 13, 16, 18]
Threes = [6, 9, 12, 15, 17, 19]

def checksum(isbn)
  # https://en.wikipedia.org/wiki/ISBN
  ones = isbn.chars.each_with_index.map {|e, n| e if Ones.include?(n) }.compact
  threes = isbn.chars.each_with_index.map {|e, n| e if Threes.include?(n) }.compact
  cs = (10 - ((ones.map {|n| n.to_i}.sum + threes.map {|n| n.to_i*3}.sum) % 10))
  cs == 10 ? "0" : cs.to_s
end

# a couple of quick sanity checks
raise "Bad checksum" unless checksum("ISBN 978-0-306-40615") == "7"
raise "Bad checksum" unless checksum("ISBN 978-0-131-17705") == "5"

def rs(length)
  (1..length).map { rand(0..9) }.join + '-'
end

def random_isbn
  digits = rs(3) + rs(1) + rs(3) + rs(5)
  "ISBN " + digits + checksum(digits)
end

Books.destroy_all

20.times {
    book = Book.create!(
      author: Faker::Name.name,
      title: Faker::Book.title,
      isbn: random_isbn
    )
}
