select a1.studentName,
       SUBSTR(a1.studentName, 1, INSTR(a1.studentName, ' ') - 1) AS first_name,
       SUBSTR(a1.studentName, INSTR(a1.studentName, ' ') + 1) AS last_name,
--       INSTR  (a1.classStartTime, '@') as start_time_pos,
--       SUBSTR (a1.classStartTime, INSTR  (a1.classStartTime, '@')) AS start_time1,
--       replace(SUBSTR (a1.classStartTime, INSTR  (a1.classStartTime, '@')), '@ ', '') AS start_time,
       lower(replace(SUBSTR (a1.classStartTime, INSTR  (a1.classStartTime, '@')), '@ ', '')) AS start_time,
       a1.*
from   attendance a1
where  a1.badgeNumber = 1006