document.querySelector("#search").addEventListener("change", (e) => {
    const recommandations = document.getElementById("recommandations")
    const lis = [...recommandations.getElementsByTagName("li")];
    const value = e.target.value.toLowerCase();
    lis.forEach( (li) => {
        const labels = [...li.getElementsByTagName("label")]
        labels.forEach((label) => {
            if (label.innerHTML.toLowerCase().includes(value)) {
                li.style.display="flex";
            } else {
                li.style.display = "none";
            }
        })
    })

})