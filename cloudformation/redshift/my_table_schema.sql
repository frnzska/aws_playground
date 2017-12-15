CREATE TABLE my_test_data
(
    id                       BIGINT DISTKEY,
    first_name               TEXT ENCODE LZO,
    last_name                TEXT ENCODE LZO,
    email                    TEXT ENCODE LZO,
    gender                   TEXT ENCODE LZO,
    ip_address               TEXT ENCODE LZO
) sortkey(id);
