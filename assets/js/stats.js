var color = Chart.helpers.color;

makeChartData = (data_id, style, label) => {
    var data = JSON.parse(document.getElementById(data_id).innerHTML);
    return {
        labels: Object.keys(data),
        datasets: [Object.assign({
            label: label,
            data: Object.values(data),
        }, style)]
    }
}

new_chart = (elem_id, data_id, title, type, style, label) => {
    const ChartData = makeChartData(data_id, style, label)
    var ctx_format = document.getElementById(elem_id).getContext('2d');
    window.charts.push(
        new Chart(ctx_format, {
            type: type,
            data: ChartData,
            options: {
                responsive: true,
                title: {
                    display: true,
                    text: title,
                    verticalAlign: "center",
                    dockInsidePlotArea: true
                }
            }
        })
    )
}

new_doughnut = (elem_id, data_id, title) => {
    const backgroundColor = [
        '#ffa725',
        '#2fa0f2'
    ]
    new_chart(elem_id, data_id, title, 'doughnut', {backgroundColor: backgroundColor}, 'data')
}

new_bar_chart = (elem_id, data_id, title, type_) => {
    if (type_ === undefined) {
        type_ = 'bar'
    }
    new_chart(
        elem_id,
        data_id,
        '',
        type_,
        {
            backgroundColor: color('#ffa725').alpha(0.5).rgbString(),
            borderColor: '#ffa725',
            borderWidth: 1
        },
        title
    );
}

document.addEventListener('DOMContentLoaded', e => {
    window.charts = [];
    new_bar_chart('subscriptions_chart', 'subscriptions', '# inscrits')
    new_doughnut('user_formats', "media", 'Média')
    new_doughnut('user_frequencies', "frequence", 'Fréquence')
    new_bar_chart(
        'decouverte_chart',
        'decouverte',
        "Avis sur les recommandations reçues dans les bulletins d'information Ecosanté (sur la base des réponses au questionnaire de satisfaction)",
        "horizontalBar"
    )
})