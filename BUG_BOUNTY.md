# OpShin Bug Bounty Program

The OpShin Bug Bounty program is in place to ensure the quality of the quality of the OpShin
ecosystem code base by incentivising contributions using rewards paid out in ADA.
Read on to learn how to participate and earn from your open source contributions!

## Introduction

The OpShin Bug Bounty Program is an initiative designed to encourage and reward contributions from our community towards improving the security and functionality of our project. By identifying, reporting and solving usability issues and suggesting new features or enhancements, participants can help us maintain the integrity and innovation of our platform. Our program is open to anyone with the skills to detect issues or propose valuable updates. By participating, you not only contribute to the project's success but also have the opportunity to earn rewards.

## Participation Guidelines

### Scope of the Program

The scope of our Bug Bounty Program includes, but is not limited to:

- **Security Vulnerabilities:** Identifying and resolving potential security threats that could compromise the security, correctness or soundness of OpShin compiled smart contracts.
- **Functional Bugs:** Solbing bugs that affect the functionality of our platform, leading to incorrect behavior or results.
- **Feature Additions:** Adding new features or enhancements that improve the experience of interacting with the OpShin platform.

Discovered issues and feature suggestions will be tagged with prices directly in the GitHub repository issues of [OpShin](https://github.com/opshin/opshin/issues) or any other part of the [OpShin ecosystem](https://github.com/opshin). These tags represent the monetary value of each task, based on its complexity and impact. The value is paid out to implemented solutions that are proposed as Pull Requests to the respective repository and accepted by a code maintainer.

### Eligibility Criteria

To be eligible to participate in the Bug Bounty Program, individuals must:

1. **Understand the Scope:** Ensure their submissions are within the defined scope of the program.
2. **Provide Reports:** Submit comprehensive and reproducible reports for bug fixes or added features, along with test cases that cover the reported issue or demonstrate the new feature.
3. **Adhere to Rules:** Follow the program rules and guidelines, including any legal or ethical standards.
4. **Public Contribution:** Be willing to publicly post a comment and open a Pull Request (PR) to claim the bounty. The claim is confirmed once the PR is accepted and merged by a code maintainer.

Moreover, any reported vulnerabilities must not have been exploited or in any way been abused by the party suggesting the fix in order to receive a reward.
Note that it is _not_ necessary to solve an existing issue in order to be eligible for a reward, we reserve the right to directly allocate a prize for created self-motivated contributions.
Solving open and prized out issues simply provides better security about the received rewards.

### Bounty Claim Process

Participants can claim a bug bounty or suggest a feature by following these steps:

1. **Identify an Issue or Feature:** Look for open issues or potential new features that are tagged with a price in the GitHub repository issues of [OpShin](https://github.com/opshin/opshin/issues) or any other part of the [OpShin ecosystem](https://github.com/opshin).
2. **Post a Comment:** To claim an issue or propose a feature, post a comment on the issue thread expressing your intent to work on it. By posting a comment, you automatically lock the issue for yourself without further approval required from any code maintainer. You will have a week to work on the issue or feature before it is re-opened to other contributors. Make sure to check that no one else claimed the issue less than a week ago.
3. **Open a Pull Request (PR):** Submit your fix or feature suggestion through a PR. Ensure your submission meets the project's quality and coding standards by providing test cases and documentation.
4. **Review and Payout:** Once your PR is accepted and merged, the tagged price will be paid out as per the bounty details. We reserve the right to increase the bounty upon request by the contributor if it is reasonably shown that the scope of the contribution exceeds the originally expected scope. Moreover we reserve the right to conduct partial payouts upon request and reasonable justification.

We generally reserve the right to pause or decline a payout in the case of incorrect or inconsistently prized out values due to i.e. typos, depletion of the Catalyst Funding provided Bug Bounty amount or similar issues. Naturally we will hope to never have to make use of this clause, to ensure a reliable and smooth experience for contributors.

Our Bug Bounty Program aims to foster a collaborative and rewarding environment for contributors. By participating, you help us enhance the security and functionality of our platform while earning rewards for your valuable contributions.


## Program Outline

### Issue Categories

We distinguish a range of issues based on their scope and complexity.
We aim to provide a reasonable bounty for every category.
The categories are (in increasing amount of allocated prize):

| Category                | Reward Range    | Comments                                                                                                                                                                                         | Example Issues                                                                                                                       |
|-------------------------|-----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| Dependency Bumps        | 0 - 200 ADA     | Most Dependency Bumps are performed automatically by Dependabot. More intricate bumps that require code changes may justify rewards similar to minor issues.                                     | https://github.com/OpShin/opshin/issues/343                                                                                          |
| Minor Issues            | 200 - 400 ADA   | Minor issues with the UX or simple bugs that can be resolved by changing a single function in the source code.                                                                                   | https://github.com/OpShin/opshin/issues/336, https://github.com/OpShin/opshin/issues/338                                             |
| Medium Issues           | 400 - 2000 ADA  | Most of the issues fall in this category. This covers bugs that require larger code base refactorings or additions of entire features that require additional modules.                           | https://github.com/OpShin/opshin/issues/333, https://github.com/OpShin/opshin/issues/301, https://github.com/OpShin/opshin/issues/68 |
| Major Issues            | 2000 - 4000 ADA | Entirely independent projects or major components of a platform like an additional website, completely overhauled software architecture etc.                                                     | https://github.com/OpShin/opshin/issues/344, https://github.com/OpShin/opshin/issues/346                                             |
| Security Vulnerabilities | 3000 - 4000 ADA | Newly discovered inconsistencies in the compiler, violations of the Python semantics preservation guarantee and similar issues that could lead to loss of user funds in production environments. | https://github.com/OpShin/opshin/pull/361, https://github.com/OpShin/opshin/pull/298                                                 |

## Report on other Bug Bounty platforms

### Bug Bounties and Issue Resolution in GitCoin

GitCoin's approach to bug bounties and issue resolution reflects its open-source ethos, encouraging collaboration and transparent communication within its community. This structure is designed to maximize the efficiency and effectiveness of resolving bugs and enhancing security, leveraging the global talent pool available in the open-source ecosystem.

#### Bug Bounty Program Structure

The GitCoin Security Bounty Program is explicitly designed to reward researchers and developers who identify and report security vulnerabilities within GitCoin's platform. Participation in the program requires adherence to a set of guidelines aimed at responsible investigation and reporting, including, but not limited to:

-   Utilizing one's own account for testing issues.
-   Avoiding destructive testing methods such as data destruction or service denial.
-   Reporting vulnerabilities privately and professionally to GitCoin's engineering team.
-   Abstaining from public disclosure of vulnerabilities until after GitCoin has addressed the issue.

Eligible reports receive rewards, with the GitCoin team retaining final judgment over the payout details, including the severity and classification of the vulnerability​ (Gitcoin Support)​.

#### Issue Resolution via Bounties

GitCoin streamlines the process of funding and resolving issues through its integration with GitHub and Ethereum blockchain. Issue funders, using the MetaMask browser extension, can create a repository on GitHub, specify the bounty for resolving an issue, and wait for a developer to address the concern. This process culminates in the bounty being held in escrow on the blockchain until the contributor's solution is approved and the funds are released.

The platform supports various project types for bounties, such as Traditional, Contest, and Cooperative, each defining how contributors are rewarded. Permission levels can be set to either allow any developer to start working on an issue or require applications and approvals. The bounty setup process involves specifying the issue details, project type, permission level, and the bounty amount, in addition to setting the expected experience level of the developer and the project's duration​ (Gitcoin)​.
Decentralization and Open Source Focus

GitCoin's decentralized nature, powered by blockchain technology, ensures that developers receive the majority of the value they create without intermediary deductions. This approach contrasts with centralized platforms like HackerOne, which, while effective in their domain, operate within a traditional corporate structure. GitCoin's method aligns with the principles of open-source development, promoting a community-driven model that rewards contributors directly for their work.

By operating on the Ethereum blockchain and facilitating payments in cryptocurrencies, GitCoin not only accelerates the transaction process but also extends its reach globally, bypassing traditional banking barriers. This inclusivity allows for a broader participation base, leveraging a diverse range of talents and insights to improve software security and development outcomes​ (Gitcoin)​.

In summary, GitCoin's bug bounty and issue resolution framework epitomize the open-source spirit, combining transparency, efficiency, and global inclusivity to foster a safer and more vibrant development ecosystem.

### GitPay

#### Introduction
GitPay is an innovative platform designed to enhance collaborative software development by connecting project owners with developers through a bounty-based issue resolution system. This approach not only accelerates problem-solving within projects but also provides a financial incentive for contributors. By facilitating the import of issues from Git repositories, GitPay streamlines the process of issue resolution, from submission to payment, fostering a more productive and engaged development community.

#### How GitPay Works

##### Issue Import and Bounty Setup
- **Project owners import issues** from their Git repositories to GitPay.
- Owners can **set deadlines and bounties** for each issue, which are then advertised to the GitPay community.

##### Collaboration and Solution Submission
- **Contributors and freelancers apply** to solve imported issues by sending offers.
- Project owners **assign tasks** to the most suitable applicants.
- Once a solution is submitted, the project owner **reviews the work**. If approved, the solution is merged into the project.

##### Payment and Integration
- **Payment is released** to the contributor once the solution is approved and merged.
- GitPay supports **payments via Credit Card or PayPal**, ensuring a smooth transfer process to the contributor's bank account.
- The system is designed to be easily integrated with existing development tools, streamlining the workflow for both project owners and contributors.

##### Benefits of Using GitPay

- Provides an **efficient mechanism** for addressing and solving project issues.
- **Incentivizes contributors** with financial rewards, attracting a wider pool of talent.
- **Facilitates collaboration** among developers from various backgrounds.
- Offers an **alternative revenue stream** for developers and enhances portfolio exposure.
- **Streamlines payment processing** and integration with development tools.

#### Community Engagement and Support

- GitPay encourages community interaction through its **Slack channel**, allowing for real-time communication and collaboration among users.
- The platform has already seen significant engagement, with **$7,377 paid in bounties** for 325 tasks to a community of 3,260 users.

#### Conclusion

GitPay represents a compelling solution for project development challenges by leveraging the power of community collaboration and financial incentives. Its user-friendly interface, coupled with the integration of popular payment methods, makes it an attractive option for both project owners seeking to resolve issues and developers looking for new opportunities.

For more information, visit GitPay at [GitPay](https://gitpay.me).

## Lessons learnt

- Usage of an integrated payment system: Both GitCoin and GitPay use integrated payment systems for awarding contributors after their contribution. GitCoin uses Ethereum wallets and GitPay credit cards. Neither of these are applicable for Cardano Wallets at the moment but this could be an interesting follow up topic.
- Providing a platform for discussion about issues: GitPay provides a dedicated Slack channel for communication about topic resolution. We do offer a discord server next to the option to discuss directly on the GitHub issue, which is more transparent and focused on the problem at hand.
- Allocation of tasks to developers: GitPay allows bounty writers to directly allocate a task to a contributor. We draw inspiration from this and automatically lock issues for developers upon request.

## Conclusion

In conclusion, the OpShin Bug Bounty Program stands as a pivotal component of our commitment to maintaining a secure and innovative ecosystem. By inviting contributions from the wider community and offering tangible rewards for their efforts, we ensure the continual enhancement of our platform. This approach not only incentivizes skilled individuals to contribute but also fosters a culture of collaboration and open-source development. Drawing inspiration from successful platforms like GitCoin and GitPay, we've tailored our program to meet the unique needs of the OpShin community while embracing best practices such as integrated payment systems and a transparent, discussion-friendly environment. As we move forward, we remain dedicated to refining our Bug Bounty Program, embracing community feedback, and exploring new avenues to make contributing to the OpShin ecosystem even more rewarding. Through this initiative, we are not just fixing issues or adding features; we are building a stronger, more resilient platform that benefits all stakeholders in the OpShin ecosystem.