import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()

class UserFactory(DjangoModelFactory):

    class Meta:
        model = User 

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.Sequence(lambda n: f'user{n}') # user0, user1...
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    timezone = 'UTC'
    is_verified = False 
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or 'TestPass123!')
 
