CREATE TABLE paging_test(
    value TEXT,
    ranking INTEGER
);

CREATE VIRTUAL TABLE paging_test_idx USING fts4(
    content="paging_test",
    value
);

CREATE TRIGGER test_bu BEFORE UPDATE ON paging_test
BEGIN
    DELETE FROM paging_test_idx WHERE docid=OLD.rowid;
END;

CREATE TRIGGER test_bd BEFORE DELETE ON paging_test
BEGIN
    DELETE FROM paging_test_idx WHERE docid=OLD.rowid;
END;

CREATE TRIGGER test_au AFTER UPDATE ON paging_test
BEGIN
    INSERT INTO paging_test_idx(docid, value) VALUES(NEW.rowid, NEW.value);
END;

CREATE TRIGGER test_ai AFTER INSERT ON paging_test
BEGIN
    INSERT INTO paging_test_idx(docid, value) VALUES(NEW.rowid, NEW.value);
END;
