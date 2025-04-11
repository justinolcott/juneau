# DynamoDB for User Chats
We will be using DynamoDB to store the textual conversations users have. This page contains some notes and some reasoning,
as well as demonstrates the structure of the tables/entries. These are very shallow tables,

> [!NOTE]
> For examples/to learn about DynamoDB structures read this great [docs page](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html).

___
Our table might look like this:
```
UserConversations

{
    "user_id": 15551112222,
    "chat_id": 0001
    "langauge": "en"
    "content": {...}
}

{
    "user_id": 15553334444,
    "chat_id": 0001
    "langauge": "de"
    "content": {...}
}

{
    "user_id": 15556667777,
    "chat_id": 0001
    "langauge": "es"
    "content": {...}
}

{
    "user_id": 15556667777,
    "chat_id": 0002
    "langauge": "es"
    "content": {...}
}
```
<sup>Fig 1. A proposed DynamoDB table structure for a user conversations in JSON representation .</sup>

In this instance, our table is names `UserConversations`. 
The primary key is not a simple partition key, but rather a composite primary key, composed of 
two attributes: `user_id` and `chat_id`, in this case both type int/number.
You likely noticed the content attribute is holding an elipses right now. Lets dig deeper into that:
```
{...
    "content": {
        <proposed schema here; TBD>
    }
}
```
<sup>Fig 2. A proposed attribute structure for the content of a user conversations in JSON representation .</sup>
___
### TODO:
- ~~What is the `scope` parameter doing in the [`__init__` function](./dynamo_db.py)?~~
    - It's used for a construct tree created by AWS, bc every construct exists w/in a heirarchy. e.g., "Place this thing (DynamoDBTable) inside that thing (JuneauStack) in the tree."
- Do we need to pass id/recipient into [`**kwargs`](./dynamo_db.py)? 
- ~~How do we add a sort key?~~
- ~~How do we grant the lambda permissions to read and write to the table?~~
    - Perhaps done in app stack already, circa line 161.
- We also need some way to store the _current_ conversation id, i.e., the `sort` key. Would this be best done with a second table using a simple primary index?
- What will the conversation content storage look like?
- How do we test the whole system?

