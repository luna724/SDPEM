# 


def click(
    elm_id: str
):
    return """
() => {
    const button = document.getElementById('$ELM_ID');
    if (button) {
        button.click();
        return [true];
    } else {
        console.warn("Button not found (id: $ELM_ID)");
        return [false];
    }
}
""".replace("$ELM_ID", elm_id)