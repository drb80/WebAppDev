----
    EACCES error in Puma or while testing on Windows.
<details>
<summary>Fix</summary>
Sometimes a reload in the browser works, but not always.

For Puma, change the line in config/puma.rb from
```
max_threads_count = ENV.fetch("RAILS_MAX_THREADS") { 5 }
```
to
```
max_threads_count = ENV.fetch("RAILS_MAX_THREADS") { 1 }
```
Puma appears to be thread unsafe in some circumstances.

For testing, comment out the line

```
  parallelize(workers: :number_of_processors)
```

in test/test\_helper.rb
</details>

----
```
None of the paths included in TZInfo::DataSources::ZoneinfoDataSource.search_path are valid zoneinfo directories. (TZInfo::DataSources::ZoneinfoDirectoryNotFound)
```
<details>
<summary>Fix</summary>
Comment out part of the line

```
gem "tzinfo-data", platforms: %i[ mingw mswin x64_mingw jruby ]
```

so it looks like

```
gem "tzinfo-data" #, platforms: %i[ mingw mswin x64_mingw jruby ]
```
</details>

----
    An error occurred while installing psych (5.1.0), and Bundler cannot continue.

    In Gemfile:
      debug was resolved to 1.8.0, which depends on
        irb was resolved to 1.8.1, which depends on
          rdoc was resolved to 6.5.0, which depends on
            psych

<details>
<summary>Fix</summary>
You need to install a YAML library:
```
    sudo apt install libyaml-dev
```
or
```
    apk install yaml-dev
```
</details>

----
    NameError: uninitialized constant Gem::Source
<details>
<summary>Fix</summary>
gem update --system
</details>

----
When testing:

    BooksLibrariesControllerTest#test_should_create_books_library: NameError: Rails couldn't find a valid model for BooksLibrary association.  Please provide the :class_name option on the association declaration. If :class_name is already provided, make sure it's an ActiveRecord::Base subclass.
<details>
<summary>Fix</summary>
Add a class\_name to the has\_many's before the has\_many through's

    class Book < ApplicationRecord
      has_many :books_libraries, class_name: "BooksLibraries"
      has_many :libraries, through: :books_libraries
    end

    class Library < ActiveRecord::Base
      has_many :books_libraries, class_name: "BooksLibraries"
      has_many :books, through: :books_libraries
    end

    class BooksLibraries < ApplicationRecord
      belongs_to :book
      belongs_to :library
    end

I'm not really sure why this is required as it would seem the class name is obvious.
</details>

----
Podman on Windows not reinstalling correctly.
This is a bug in the Podman installer, it doesn't remove the container
directory in .config. Here's what worked for me.

    wsl --unregister podman-machine-default
    podman machine rm podman-machine-default
    del C:\users\drsjb\.config\containers\
    podman machine init
    podman machine start
----
