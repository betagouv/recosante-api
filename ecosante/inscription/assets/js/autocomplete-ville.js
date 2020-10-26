import Autocomplete from "@trevoreyre/autocomplete-js";
import "@trevoreyre/autocomplete-js/dist/style.css";


document.addEventListener("DOMContentLoaded", function(event) {
  const autocomplete = new Autocomplete('#ville_entree', {
    search: input => {
      const url = `https://geo.api.gouv.fr/communes?&boost=population&fields=nom,code&format=json&nom=${encodeURI(input)}`

      return new Promise(resolve => {
        if (input.length < 3) {
          return resolve([])
        }

        fetch(url)
          .then(response => response.json())
          .then(data => {
            resolve(data)
          })
      })
    },
    getResultValue: result => result.nom,
    onSubmit: ville => {
      document.getElementById("ville_insee").value = ville.code
      document.getElementById("ville_name").value = ville.nom
    }
  })
  autocomplete.input.addEventListener('keydown', (event) => {
      const { key } = event
      if (key == 'Enter') {
        event.preventDefault();
      }
  });

  const parent_telephone = document.getElementById('telephone').parentElement.parentElement
  parent_telephone.setAttribute('hidden', "")
  for(const input of document.getElementsByName("diffusion")) {
    input.addEventListener('change', (event) => {
      if (event.target.value === 'sms') {
        parent_telephone.removeAttribute('hidden')
      } else {
        parent_telephone.setAttribute('hidden', "")
      }
    })
  }
});