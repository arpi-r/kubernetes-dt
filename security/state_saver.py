import time

def get_current_timestamp():
    return int(time.time())

def extract_current_model(model_name):
    model_file = open(model_name, "r")
    model = model_file.read()
    return model

def extract_security_logs():
    log_file = open("security_logs.txt", "r")
    logs = log_file.read()
    return logs

def generate_model_checkpoint(model_file, model_state, logs):
    model_checkpoint = ""

    if logs:
        model_checkpoint = "Attack detected!\n\n"
        model_checkpoint += "Related AUDIT LOGS:\n\n" + logs + "\n\n\n"
    
    model_checkpoint += "Checkpoint DT MODEL:\n\n" + model_file + "\n\n\n"
    model_checkpoint += "Checkpoint DT MODEL STATE:\n\n" + model_state + "\n\n\n"

    return model_checkpoint

def save_model_checkpoint(model_checkpoint_info):
    model_checkpoint = "K8sDT_" + str(get_current_timestamp()) + ".txt"
    with open("model-checkpoints/" + model_checkpoint, 'w') as f:
        f.write(model_checkpoint_info)
    
    return model_checkpoint

if __name__ == '__main__':
    model_file = extract_current_model("../abs-k8s-model/K8sDT.abs")
    model_state = extract_current_model("../abs-k8s-model/K8sDT_output.txt")
    logs = extract_security_logs()
    model_checkpoint = generate_model_checkpoint(model_file, model_state, logs)
    model_saved = save_model_checkpoint(model_checkpoint)
    print("Model state checkpoint created: ", model_saved)
