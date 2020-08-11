import Store from 'https://cdn.jsdelivr.net/gh/DavidBruant/baredux@master/main.js'
import { html, render } from 'https://unpkg.com/htm/preact/standalone.module.js'

const NIVEAU_DIFFICULTÉ_COLUMN = 'Niveau de difficulté'

function NiveauFilter({recommz, value, setFilterValue}) {
    const key = NIVEAU_DIFFICULTÉ_COLUMN
    const values = new Set(recommz.map(r => r[key]).filter(str => str !== undefined && str !== ''))

    return html`<section>
        ${
            [...values].map(v => {
                return html`<label>
                    ${v}
                    <input type="radio" name=${key} value=${v} checked=${v === value} onChange=${e => { setFilterValue(v) }}/>
                </label>`
            })
        }
        <label>
            tous
            <input type="radio" name=${key} value="tous" checked=${value === undefined} onChange=${e => { setFilterValue(undefined) }}/>
        </label>
    </section>`
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

    filtersSection.innerHTML = '';
    ul.innerHTML = '';

    console.log('filterValues.get(NIVEAU_DIFFICULTÉ_COLUMN)', filterValues.get(NIVEAU_DIFFICULTÉ_COLUMN))

    const niveauValue = filterValues.get(NIVEAU_DIFFICULTÉ_COLUMN)
    const niveauFilter = value => {
        store.mutations.setFilterValue(
            NIVEAU_DIFFICULTÉ_COLUMN,
            value,
            value ? r => r[NIVEAU_DIFFICULTÉ_COLUMN] === value : undefined
        )
    }

    render(html`<${NiveauFilter} recommz=${recommz} value=${niveauValue} setFilterValue=${niveauFilter} />`, filtersSection)

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
