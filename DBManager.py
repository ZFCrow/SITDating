from Models import Users, db, Matches, SwipeRight, Preference

class DBManager:

    @staticmethod
    def add_user(username, password, name, age, gender, interests, course, email):
        user = Users(username=username, password=password, name=name, age=age, gender=gender, interests=interests, course=course, email=email)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_user_by_id(user_id):
        return Users.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email):
        return Users.query.filter_by(email=email).first() 
    
    @staticmethod
    def get_all_users():
        return Users.query.all()
    
    @staticmethod
    def get_all_users_except(user_id_to_exclude):
        return Users.query.filter(Users.id != user_id_to_exclude).all()


    @staticmethod
    def delete_user(user_id):
        user = Users.query.get(user_id)
        db.session.delete(user)
        db.session.commit() 

    @staticmethod
    def get_matches(user_id):
        # Query for matches where the user is either user1 or user2 directly
        matches_as_user1 = Matches.query.filter_by(user_id_1=user_id).all()
        matches_as_user2 = Matches.query.filter_by(user_id_2=user_id).all()
        
        print("User ID:", user_id)
        print("Matches as user1:", matches_as_user1)
        print("Matches as user2:", matches_as_user2)
        print("------------------------------------------------")
        # Combine the matches and extract matched users
        matched_users = []
        for match in matches_as_user1:
            matched_users.append(Users.query.get(match.user_id_2))
        for match in matches_as_user2:
            matched_users.append(Users.query.get(match.user_id_1))
        
        return matched_users

    @staticmethod
    def deleteSwipeRight(swiper_id, swipee_id): 
        swipe = SwipeRight.query.filter_by(swiper_id=swiper_id, swipee_id=swipee_id).first()
        db.session.delete(swipe)
        db.session.commit()

    @staticmethod
    def add_swipe_right(swiper_id, swipee_id):
        reciprocal_swipe = SwipeRight.query.filter_by(swiper_id=swipee_id, swipee_id=swiper_id).first()
        if reciprocal_swipe:
            print ("reciprocal swipe found")
            #delete the reciprocal swipe 
            db.session.delete(reciprocal_swipe)
            match = DBManager.add_match(swiper_id, swipee_id)
            return match
        else:
            swipe = SwipeRight(swiper_id=swiper_id, swipee_id=swipee_id)
            db.session.add(swipe)
            db.session.commit()
            return swipe 
    




    def add_match(user_id_1, user_id_2):
        match = Matches(user_id_1=user_id_1, user_id_2=user_id_2)
        db.session.add(match)
        db.session.commit()
        return match 
    
    @staticmethod
    def add_preference(user_id, preferred_age_min, preferred_age_max, preferred_gender, interests):
        preference = Preference(user_id=user_id, preferred_age_min=preferred_age_min, preferred_age_max=preferred_age_max, preferred_gender=preferred_gender, interests=interests)
        db.session.add(preference)
        db.session.commit()
        return preference 
    
    @staticmethod
    def get_user_preferences(user_id):
        return Preference.query.filter_by(user_id=user_id).first()