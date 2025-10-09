The React Native code in the book is wrong; now see: https://github.com/drb80/ReactNativeTodo

<hr/>

What Rails 7 had for mass assignment:

    params.require(:advisor).permit(:name, student_ids: [])

has changed to:

    params.expect(adivisor: [:name, student_ids: []])

