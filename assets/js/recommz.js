import Store from 'https://cdn.jsdelivr.net/gh/DavidBruant/baredux@master/main.js'

const NIVEAU_DIFFICULTÉ_COLUMN = 'Niveau de difficulté'

function makeNiveauFilter(recommz, value, setFilterValue) {
    const key = NIVEAU_DIFFICULTÉ_COLUMN
    const values = new Set(recommz.map(r => r[key]).filter(str => str !== undefined && str !== ''))

    const section = document.createElement('section')

    for (const v of values) {
        const radio = document.createElement('input')
        radio.type = "radio"
        radio.name = key;
        radio.value = v;

        radio.addEventListener('change', e => { setFilterValue(v) })

        const label = document.createElement('label');
        label.append(v, radio);
        radio.checked = v === value;

        section.append(label)
    }

    const allRadio = document.createElement('input')
    allRadio.type = "radio"
    allRadio.name = key;
    allRadio.value = 'tous';
    allRadio.addEventListener('change', e => { setFilterValue(undefined) })
    const allLabel = document.createElement('label');
    allLabel.append('tous', allRadio);
    allRadio.checked = value === undefined;

    section.append(allLabel)

    return section;
}


const store = new Store({
    state: {
        recommz: [],
        filters: new Map(),
        filterValues: new Map()
    },
    mutations: {
        setRecommz(state, recommz) {
            state.recommz = recommz;
        },
        setFilterValue(state, key, value, filter) {
            console.log('setFilterValue', key, value, filter)

            if (value !== undefined) {
                state.filterValues.set(key, value)
            }
            else {
                state.filterValues.delete(key)
            }

            if (typeof filter !== 'function') {
                state.filters.delete(key)
            }
            else {
                state.filters.set(key, filter)
            }
        }
    }
})

store.subscribe(state => {
    const { recommz, filters, filterValues } = state;
    const ul = document.querySelector('ul.recommz')
    const filtersSection = document.querySelector('.filters')

    ul.innerHTML = '';
    filtersSection.innerHTML = '';

    console.log('filterValues.get(NIVEAU_DIFFICULTÉ_COLUMN)', filterValues.get(NIVEAU_DIFFICULTÉ_COLUMN))

    const niveauFilter = makeNiveauFilter(recommz, filterValues.get(NIVEAU_DIFFICULTÉ_COLUMN), value => {
        store.mutations.setFilterValue(
            NIVEAU_DIFFICULTÉ_COLUMN,
            value,
            value ? r => r[NIVEAU_DIFFICULTÉ_COLUMN] === value : undefined
        )
    })
    filtersSection.append(niveauFilter)

    let filteredRecommz = recommz;
    for(const f of filters.values()){
        filteredRecommz = filteredRecommz.filter(f)
    }

    document.querySelector('.recommz-count').textContent = `(${filteredRecommz.length})`

    for (const { 'Recommandation': recommandation } of filteredRecommz) {
        const li = document.createElement('li')
        li.append(recommandation)
        ul.append(li)
    }
})

d3.csv('./data/recommandations.csv')
    .then(recommz => {
        console.log('recommz', recommz)

        store.mutations.setRecommz(recommz)
    })
