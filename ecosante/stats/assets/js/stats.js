import './ecosante/stats/assets/js/stats_map'

import Chart from 'chart.js';

var color = Chart.helpers.color;

const makeChartData = (data_id, style, label) => {
    var data = JSON.parse(document.getElementById(data_id).innerHTML);
    return {
        labels: Object.keys(data),
        datasets: [Object.assign({
            label: label,
            data: Object.values(data),
        }, style)]
    }
}

const new_chart = (elem_id, data_id, title, type, style, label, other_options) => {
    let data = makeChartData(data_id, style, label)
    let ctx_format = document.getElementById(elem_id).getContext('2d');
    let options = {
        ...{
            responsive: true,
            maintainAspectRatio: window.innerWidth > 565,
            title: {
                display: true,
                text: title,
                verticalAlign: "center",
                dockInsidePlotArea: true
            }
        },
        ...other_options
    }
    console.log(options)
    window.charts.push(new Chart(ctx_format, {data, options, type}))
}

const new_doughnut = (elem_id, data_id, title) => {
    const backgroundColor = [
        '#ffa725',
        '#2fa0f2',
        'rgb(75, 192, 192)',
        'rgb(255, 205, 86)'
    ]
    new_chart(elem_id, data_id, title, 'doughnut', {backgroundColor: backgroundColor}, 'data')
}

const new_bar_chart = (elem_id, data_id, title, type_, other_options) => {
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
        title,
        other_options
    );
}

document.addEventListener('DOMContentLoaded', e => {
    window.charts = [];
    new_bar_chart('subscriptions_chart', 'subscriptions', '# inscrits')
    new_doughnut('user_formats', "media", 'Média')
    new_doughnut('user_frequencies', "frequence", 'Fréquence')
    new_doughnut(
        'decouverte_chart',
        'decouverte',
        "Avis sur les recommandations reçues dans les bulletins d'information Ecosanté (sur la base des réponses au questionnaire de satisfaction)",
    )
    new_bar_chart(
        'ouvertures_chart',
        'ouvertures',
        'Taux d’ouverture des mails',
        'line',
        {
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true,
                        max: 100
                    }
                }]
            }
        }
    )
})
