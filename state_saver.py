import time

def get_current_timestamp():
    return int(time.time())

def extract_current_model_state(model_name):
    model_file = open(model_name, "r")
    model_state = model_file.read()
    return model_state

def extract_audit_logs():
    return "DUMMY AUDIT LOGS"

def add_audit_logs(model_state, logs):
    model_state_with_logs = ""

    if logs:
        model_state_with_logs = "Signature-based attack detected!\n\n"
        model_state_with_logs += "Related AUDIT LOGS:\n\n" + logs + "\n\n\n"
    
    model_state_with_logs += "Checkpoint MODEL STATE:\n\n" + model_state + "\n"

    return model_state_with_logs

def save_model_state(model_state_with_logs):
    model_checkpoint = "K8sDT_" + str(get_current_timestamp()) + ".abs"
    with open("model-checkpoints/" + model_checkpoint, 'w') as f:
        f.write(model_state_with_logs)
    
    return model_checkpoint

if __name__ == '__main__':
    model_state = extract_current_model_state("abs-k8s-model/K8sDT.abs")
    logs = extract_audit_logs()
    model_state_with_logs = add_audit_logs(model_state, logs)
    model_saved = save_model_state(model_state_with_logs)
    print("Model state checkpoint created: ", model_saved)
