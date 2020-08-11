import Store from 'https://cdn.jsdelivr.net/gh/DavidBruant/baredux@master/main.js'
import { html, render } from 'https://unpkg.com/htm/preact/standalone.module.js'

const NIVEAU_DIFFICULTÉ_COLUMN = 'Niveau de difficulté'


const RECOMMANDABILITÉ_COLUMN = 'Recommandabilité'
const RECOMMANDABILITÉ_UTILISABLE = `Utilisable`


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

function RecommandabilitéFilter({recommz, checked, setFilterValue}){
    const key = RECOMMANDABILITÉ_COLUMN
    const values = new Set(recommz.map(r => r[key]).filter(str => str !== undefined && str !== ''))

    return html`<section>
        ${
            [...values].map(v => {
                return html`<label>
                    ${v}
                    <input type="checkbox" name=${key} value=${v} checked=${checked.has(v)} onChange=${e => { setFilterValue(v) }}/>
                </label>`
            })
        }
    </section>`
}


const store = new Store({
    state: {
        recommz: [],
        filters: new Map(Object.entries({
            [RECOMMANDABILITÉ_COLUMN]: 
                r => store.state.filterValues.get(RECOMMANDABILITÉ_COLUMN).has(r[RECOMMANDABILITÉ_COLUMN])
        })),
        filterValues: new Map(Object.entries({
            [NIVEAU_DIFFICULTÉ_COLUMN]: undefined,
            [RECOMMANDABILITÉ_COLUMN]: new Set([RECOMMANDABILITÉ_UTILISABLE])
        }))
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
    
    const recommandabilitéFilterFunction = selectedValue => {
        const valuesSet = filterValues.get(RECOMMANDABILITÉ_COLUMN);

        if(valuesSet.has(selectedValue)){
            valuesSet.delete(selectedValue)
        }
        else{
            valuesSet.add(selectedValue)
        }

        store.mutations.setFilterValue(
            RECOMMANDABILITÉ_COLUMN,
            valuesSet,
            r => valuesSet.has(r[RECOMMANDABILITÉ_COLUMN])
        )
    }

    const niveauFilterFunction = value => {
        store.mutations.setFilterValue(
            NIVEAU_DIFFICULTÉ_COLUMN,
            value,
            value ? r => r[NIVEAU_DIFFICULTÉ_COLUMN] === value : undefined
        )
    }

    render(html`
        <${NiveauFilter} recommz=${recommz} value=${filterValues.get(NIVEAU_DIFFICULTÉ_COLUMN)} setFilterValue=${niveauFilterFunction} />
        <${RecommandabilitéFilter} recommz=${recommz} checked=${filterValues.get(RECOMMANDABILITÉ_COLUMN)} setFilterValue=${recommandabilitéFilterFunction} />
    `, filtersSection)

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
