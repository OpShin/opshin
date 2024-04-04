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
- **Feature Additions:** Adding new features or enhancements that improve the experience of interacting with the OpShin platoform.

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
| Security Vulnerabilites | 3000 - 4000 ADA | Newly discovered inconsistencies in the compiler, violations of the Python semantics preservation guarantee and similar issues that could lead to loss of user funds in production environments. | https://github.com/OpShin/opshin/pull/361, https://github.com/OpShin/opshin/pull/298                                                 |