Useful Links

* Starknet Docs: https://docs.starknet.io/
* Cairo Tutorials: https://book.cairo-lang.org/
* Landing Page: https://bitcoinxprivacy.com
* DoraHacks: https://dorahacks.io/hackathon/bitcoinxprivacy/detail

Useful Links & Resources

🌐 Hackathon Info

*Landing Page: https://hackathon.starknet.org
*DoraHacks (Register): https://dorahacks.io/hackathon/redefine/detail

📖 Core Documentation

*Starknet Docs: https://docs.starknet.io/
*Cairo Book: https://book.cairo-lang.org/

🎓 Learning

*Starknet Academy: https://academy.starknet.org/
*Founder Basecamp (YouTube): https://www.youtube.com/playlist?list=PLMXIoXErTTYXsCAom53zuk_A_W25KHT0I

🔐 Privacy Tools

*Starknet Privacy Toolkit: https://github.com/omarespejel/starknet-privacy-toolkit
*Tongo SDK Quick Start: https://docs.tongo.cash/sdk/quick-start.html
*Tongo Protocol Intro: https://docs.tongo.cash/protocol/introduction.html
*Sumo Login (ZK social login): https://github.com/fatlabsxyz/sumo-login-cairo
*Garaga Documentation: https://garaga.gitbook.io/garaga
*Garaga npm package: https://www.npmjs.com/package/garaga
*Scaffold-Garaga: https://github.com/KevinSheeranxyj/scaffold-garaga
*Semaphore Protocol: https://semaphore.pse.dev/

₿ Bitcoin & DeFi Tools
*LayerSwap Starknet Docs: https://docs.layerswap.io/integration/UI/Widget/Starknet/Starknet
*Atomiq Docs: https://docs.atomiq.exchange/
*Garden Docs Quickstart: https://docs.garden.finance/developers/sdk/nodejs/quickstart
*Vesu Developer Docs: https://docs.vesu.xyz/developers
*Starknet Bitcoin DeFi: https://www.starknet.io/blog/bitcoin-defi-domain/
*Xverse Starknet Bridge: https://www.xverse.app/blog/starknet-bridge
*Xverse Starknet Wallet: https://www.xverse.app/starknet-wallet
*Ekubo Docs: https://docs.ekubo.org/

🛠 OpenZeppelin
*Cairo Contracts: https://github.com/OpenZeppelin/cairo-contracts
*Cairo Docs: https://docs.openzeppelin.com/contracts-cairo
*Contracts Wizard for Cairo: https://wizard.openzeppelin.com/cairo

⚙️ Development Frameworks
*Scaffold-Stark: https://github.com/Scaffold-Stark/scaffold-stark-2
*Scaffold-Stark Docs: https://scaffoldstark.com/docs
*StarknetKit: https://www.starknetkit.com/

🎥 Workshops (Video)
*Privacy Preserving Apps Workshop: https://www.youtube.com/watch?v=vgawLi0gT98
*ZK-SNARK Verification Workshop: https://www.youtube.com/watch?v=TxFLvXvYByM

💬 Community & Support
*Starknet Discord: https://discord.com/invite/starknet-community
*Garaga Telegram: https://t.me/GaragaPairingCairo
*Vesu Discord: https://discord.gg/G9Gxgujj8T
*Vesu Telegram: https://telegram.me/VesuChat

Curated Hacker Ideas – What can you build?

Check out all the curated ideas at hackathon.starknet.org

🔐 PRIVACY TRACK

ZK Protocol Implementations
- Implement Semaphore on Starknet – Port the Semaphore protocol to Cairo for anonymous group membership and signaling
- Build Cairo verifiers for Sigma protocols – Implement zero-knowledge Sigma protocol verifiers in Cairo
- Mental Poker implementation – Provable card shuffles under encryption, foundation for hidden-info games
- Anonymous credentials system – Prove attributes (age, membership) without revealing identity

Games with Private State
- Poker / card game with hidden hands – Players cannot see each other cards, provably fair
- Strategy game with fog of war – Hidden game state between players
- Liar's poker or bluffing games – Games where lying is part of the mechanic

Private DeFi & Commerce
- Sealed-bid auction – Hidden bids until reveal, prevents front-running
- Dark pool / private orderbook – Hide trade intent, MEV protection
- Private prediction market – Hidden positions until market resolution

Private Governance
- Private voting system – Hide votes until tally, prove eligibility without revealing identity

Confidential Transactions
- Private payment app using Tongo – Confidential ERC20 transfers using ElGamal encryption and ZK proofs
- Shielded wallet UI – Deposit/withdraw/transfer flows using StarkWare SDK
- Privacy-first DeFi frontend – Private swaps, lending UIs

ZK Proof Verification
- Verify Noir proofs on Starknet – Build a ZK app in Noir, deploy verifier using Garaga
- Verify Circom/Groth16 proofs on Starknet – Port existing Circom circuits to Starknet verification

Onboarding and Identity
- ZK social login dApp using Sumo Login – Onboard users with JWT proofs, no seed phrases

₿ BITCOIN TRACK

Yield & Vaults
- BTC yield vault – Intake BTC wrapper, borrow against it, deploy into stables, return yield
- Tokenized BTC yield representation – Create a token representing yield-bearing BTC position
- Vault curator/manager system – Curate and manage BTC vault strategies
- Leverage looping for BTC – Automated leverage strategies for BTC holders

Private BTC DeFi
- Private BTC swap – Trade BTC without revealing amounts
- Private lending with BTC collateral – Borrow stables against BTC privately
- Private yield on BTC – Earn yield without revealing position size
- Private yield on stables – Earn yield on USDC privately

BTC Primitives
- BTC-backed CDP – Mint stablecoins against BTC collateral
- BTC DCA (Dollar Cost Average) tool – Automated BTC purchases on Starknet
- BTC staking interface – Stake wrapped BTC and earn STRK

Infrastructure
- Cross-chain BTC bridge UI – Improved UX for bridging BTC to Starknet

🚀 OPEN TRACK

Build any innovative product on Starknet:
- Gaming
- Social apps
- Payments
- Consumer apps

Full details: hackathon.starknet.org

hey hackers!

Quick tooling drop for your Re{define} builds: StarkZap is a TypeScript SDK that packages everything you need to integrate with Starknet in minutes, no Cairo required.

What's included:

* Wallets: Privy social login (Google, etc.) + Cartridge Controller support
* Paymaster: Gasless transactions via AVNU (your users never buy tokens)
* Staking: Pool discovery, stake/claim/exit delegation pools (STRK staking ready)
* ERC20 ops: Transfers, batch transfers, balance queries
* Transaction builder: Batch multiple ops into one atomic tx

Works in Node.js, browsers, and React Native. Mainnet + Sepolia + local devnet.

Useful for hackathon tracks like: BTC yield vaults, staking interfaces, private DeFi frontends, payment apps, anything where you need wallet infra + on-chain interactions without building from scratch.

Links:
* GitHub: https://github.com/keep-starknet-strange/x
* Docs: https://docs.google.com/document/d/1e7CWkQwjHw4CS-KCMe1sT2UUnGesXJUZGlTDqeUhEN0/edit?tab=t.0

Happy building!