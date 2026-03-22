# LibTracker

> **Developed by Rebs Dev** > **Team Members:** Sirac Ketenoğlu, Emre Turan, Barış Küçükkaya, Reis Yıldız

---

## Project Vision & Problem Statement
> *Contribution by: Emre*

There is a high population of students and a little amount of space to study in libraries. Finding a place to study is a painful experience for students, particularly during working hours. For university students who are in need of finding free spaces to study, **LibTracker** is an application that checks the busyness of libraries. Unlike other competitors, our product saves students’ time and makes it accessible.

## Target Users & Stakeholders

* **University Students:** To check library busyness levels and plan their study time efficiently.
* **Exam-period Students:** To find less crowded places for studying.
* **Library Management:** To analyze library use patterns and manage resources more effectively.
* **University Administration:** To improve students’ academic productivity.

## Key Features
> *Contribution by: Sirac*

* **Live Tracking:** Displaying the current occupancy status of the library.
* **Making Reservations:** Enabling students to book a seat or study area in advance to secure their spot, especially during peak hours.
* **Interactive System:** Sending user feedback regarding busyness.
* **Data Analysis:** Showing hourly and daily statistics.

## Architecture & Technology Stack
> *Contribution by: Barış*

LibTracker utilizes a **Layered Architecture**. This structure was chosen because it is understandable, easily implemented by juniors, and easier to maintain compared to other architectures.

*  **Presentation Layer (Frontend):** A Web UI developed using **JavaScript, CSS, and HTML**.
*  **Application Layer (Backend):** A REST API built with **Python**, handling Authentication & Validation, Occupancy Service, and Statistics Service.
*  **Data Layer (Database):** A **MySQL** Database system.
*  **Version Control:** **GitHub**.

##  Quality Attributes
> *Contribution by: Reis*

* **Simplicity:** There are various types of users for this app, so everyone should understand and use it easily to save time as intended.
* **Accuracy:** The program is completely based on accuracy, so every piece of information that the program provides has to be accurate to improve user satisfaction.
* **Scalability:** The system should not crash in the case of a large amount of users at certain timespans, such as final weeks.
