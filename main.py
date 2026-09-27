from students import add_student, view_students, update_student, delete_student


print("================================")
print("        Welcome to CampusHub")
print("================================")


while True:

    print("\n1. Add Student")
    print("2. View Students")
    print("3. Update Student")
    print("4. Delete Student")
    print("5. Exit")

    choice = input("\nEnter your choice: ")

    if choice == "1":

        name = input("Enter student name: ")
        roll_no = input("Enter roll number: ")
        course = input("Enter course: ")
        email = input("Enter email: ")

        add_student(name, roll_no, course, email)

    elif choice == "2":

        view_students()

    elif choice == "3":

        student_id = input("Enter student ID to update: ")

        name = input("Enter new name: ")
        roll_no = input("Enter new roll number: ")
        course = input("Enter new course: ")
        email = input("Enter new email: ")

        update_student(student_id, name, roll_no, course, email)

    elif choice == "4":

        student_id = input("Enter student ID to delete: ")

        delete_student(student_id)

    elif choice == "5":

        print("Thank you for using CampusHub!")
        break

    else:

        print("Invalid choice! Please try again.")