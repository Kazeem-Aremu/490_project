# ADR 1: Storage Decisions

## Purpose 
The purpose of this document is to detail our decisions making process surrounding how we choose to store data for this project.

## Status : Accepted

## Context 
This project requries the movement, storage, and processing a large amount of data. In the class room this would be enough to have a CSV file to store our test accounts and thier related data. However as our capstone project meant to mock or even potentially be a released project that can be used by the public we need to look for maintanability, scalability, and development ease.

### Options 
| Option | Parent Company | Hosting Responsibility | Ease of Use | Cost | Additional Benefits |
|--------|---------|--------------|-------------|------|---------------------|
| Supabase | Private | Company | Easy |Free - $25/Month | Authentication, Easy to use Documentation, Prewritten Functions/API, PostgreSQL, Hosting|
| FireBase | Google/Alphabet | Company | Medium | Free/Pay as you go | Documentation, Cloud Hosting, Scalability, Realtime Database  |  
| Windows SQL Server| Windows | Developer | Hard | Free - Pay as you go| Works with AZURE services, fully customizable to our needs  | 

Based on this information and the team's experince we will make our decision as to which data service to use.

## Decision

The team has decided to use Supabase for the project. The reason this decision was made was primarily due to the experience of the team. While we have all taken a course in database management that tought us to use Windows SQL server, in practice we have experince using Firebase and Supabase. Supabase was chosen because of its PostgreSQL database and because of existing tools our team has developed to interface with it.

## Consequences

1. Development time will be sped up since we don't have to create our own database infrastructure. 
2. Our login process will be simplified and will be unified with our database allowing easy access to account information by authorized users.
3. We will have less freedom as to the particulars of how login and database are implemented and managed.
4. Updates from Supabase have the chance of requiring we change our API.

