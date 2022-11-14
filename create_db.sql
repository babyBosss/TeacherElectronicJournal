CREATE TABLE if not exists timetable (
                           week_numder INTEGER,
                           day_of_week INTEGER,
                           lesson_number INTEGER,
                           item TEXT
);

CREATE TABLE if not exists progress (
                          week_numder INTEGER,
                          day_of_week INTEGER ,
                          id_student INTEGER REFERENCES students(id_student),
                          mark TEXT
);

CREATE TABLE if not exists students(
                         id_student INTEGER PRIMARY KEY,
                         full_name TEXT
);