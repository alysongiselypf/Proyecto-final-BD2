CREATE TRIGGER trg_eh_sync
AFTER INSERT ON medicamento
FOR EACH ROW
EXECUTE FUNCTION eh_sync_trigger();
