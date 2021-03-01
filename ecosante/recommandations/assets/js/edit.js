function selectDiv(selectedValue) {
    ['generale', 'episode_pollution', 'pollens'].forEach(
        v => {
            document.getElementById(v).style.display = ((v == selectedValue) ? 'block' : 'none')
        }
    )
}

document.addEventListener('DOMContentLoaded', _ => {
    selectDiv(document.editForm.type_.value)
    document.editForm.type_.forEach(
        r => { r.addEventListener('change', e => { selectDiv(e.target.value) }) }
    )
    document.querySelectorAll(".raz").forEach(
        b => {
            b.addEventListener('click', e => {
                e.preventDefault()
                let parent =  e.target.parentNode.parentNode
                parent.querySelectorAll("input").forEach(
                    i => {
                        if (i.type == "radio" || i.type == "checkbox") {
                            i.checked = false
                        } else {
                            i.value = null
                        }
                    }
                )
                parent.querySelectorAll("textarea").forEach(
                    t => { t.value = null }
                )
                parent.querySelectorAll("select").forEach(
                    s => s.value = ""
                )
            })
        }
    )
})