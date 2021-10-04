function selectDiv(selectedValue) {
    ['generale', 'episode_pollution', 'pollens', 'radon'].forEach(
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
    document.getElementsByName("qa").forEach(
        i => {
            i.addEventListener("change", e => {
                document.querySelectorAll(`#${e.target.id}`).forEach(
                    q => q.checked = e.target.checked
                )
            })
        }
    )
    document.querySelectorAll('.button-apercu').forEach(
        b => {
            b.addEventListener('click', e => {
                e.preventDefault()
                let parent = e.target.parentNode
                let rendu = parent.querySelector('.rendu')
                if (rendu.style.display != undefined && rendu.style.display != 'none') {
                    rendu.style.display = 'none';
                } else {
                    document.querySelectorAll('.rendu').forEach(e => e.style.display = 'none')
                    let to_render = document.getElementById(e.target.dataset.id).value
                    var form = new FormData();
                    form.append('to_render', to_render)
                    fetch(
                        '/recommandations/_rendu_markdown',
                        {
                            method: 'post',
                            body: form
                        }
                    )
                    .then(response => response.text())
                    .then(blob => {
                        rendu.innerHTML = blob
                        rendu.style.display = 'block'
                    })
                }
            })
        }
    )
    document.querySelectorAll('.rendu').forEach(e => e.style.display = 'none')
})