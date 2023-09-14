EACCES error in Puma or while testing on Windows.
<details>
For Puma, change the line in config/puma.rb from
```
max_threads_count = ENV.fetch("RAILS_MAX_THREADS") { 5 }
```
to

`max_threads_count = ENV.fetch("RAILS_MAX_THREADS") { 1 }`

Puma appears to be thread unsafe in some circumstances.


For testing, comment out the line

`  parallelize(workers: :number_of_processors)`

in test/test\_helper.rb
</details>
