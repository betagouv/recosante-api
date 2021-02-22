function selectDiv(selectedValue) {
    ['generale', 'episode_pollution', 'pollens'].forEach(
        v => {
            document.getElementById(v).style.display = ((v == selectedValue) ? 'block' : 'none')
        }
    )
}

document.addEventListener('DOMContentLoaded', _ => {
    selectDiv(document.editForm.type.value)
    document.editForm.type.forEach(
        r => { r.addEventListener('change', e => { selectDiv(e.target.value) }) }
    )
})