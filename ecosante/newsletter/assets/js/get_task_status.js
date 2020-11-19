function update_task_status() {
    const task_id = JSON.parse(document.getElementById("task_id").innerHTML)['task_id']
    const progress = document.getElementById("progress")
    const progress_details = document.getElementById("progress_details")
    fetch("./task_status/"+task_id).then(
        function(response) {
            return response.json().then(
                function(json) {
                    progress.innerHTML =parseFloat(json['progress']).toFixed(2) + '%'
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
    )
}

document.addEventListener('DOMContentLoaded', e => {
    update_task_status()
})