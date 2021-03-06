import { SELECT_TOKEN, REFRESH_BALANCES } from './actions'

const initialState = {
  tokens: {
    1: {
      name: 'Digimon Coin',
      symbol: 'DGX',
      contract_address: '0xcd234a471b72ba2f1ccf0a70fcaba648a5eecd8d',
      rate: 0.06,
      currentlyDistributed: 42000,
      totalToDistribute: 240000,
      ethReceived: 77,
    },
    2: {
      name: 'EOS',
      symbol: 'EOS',
      contract_address: '0xf778b86fa74e846c4f0a1fbd1335fe81c00a0c91',
      rate: 0.02,
      currentlyDistributed: 2307,
      totalToDistribute: 400000,
      ethReceived: 2,
    },
  },
  currentToken: 1,
  user: {},
}

const reducer = (state = initialState, action) => {
  switch (action.type) {
    case SELECT_TOKEN:
      return { ...state, currentToken: action.id }
    case REFRESH_BALANCES:
      return { ...state, user: action.payload }
    default:
      return state
  }
}

export default reducer
