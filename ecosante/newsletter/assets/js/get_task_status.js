function update_task_status() {
    const task_status_url = JSON.parse(document.getElementById("task_status_url").innerHTML)['task_status_url']
    const progress_display = document.getElementById("progress_display")
    const progress = document.querySelector("progress")
    const progress_details = document.getElementById("progress_details")
    fetch(task_status_url).then(
        async function (response) {
            const json = await response.json()
            let progress_value = parseFloat(json['progress']).toFixed(2)
            progress.value = progress_value
            progress_display.innerHTML = progress_value + '%'
            progress_details.innerHTML = json['details']
            if ("sms_campaign_id" in json) {
                progress_details.innerHTML += `<h2>Vérifiez la campagne SMS en cliquant <a href="https://my.sendinblue.com/camp/sms/${json['sms_campaign_id']}/setup">ici</a></h2>`
            }
            if ("email_campaign_id" in json) {
                progress_details.innerHTML += `<h2>Vérifiez la campagne email en cliquant <a href="https://my.sendinblue.com/camp/classic/${json['email_campaign_id']}/setup">ici</a></h2>`
            }
            if (json['state'] == 'STARTED' || json['state'] == 'PENDING') {
                setTimeout(update_task_status, 500)
            }
        }
    )
}

document.addEventListener('DOMContentLoaded', e => {
    update_task_status()
})