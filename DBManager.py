from Models import Users, db, Matches 

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
        #return matchesAsUser1 + matchesAsUser2 
        return None

    # @staticmethod
    # def add_swipe_right(swiper_id, swipee_id):
    #     swipe = SwipeRight(swiper_id=swiper_id, swipee_id=swipee_id)
    #     db.session.add(swipe)
    #     db.session.commit()
    #     return swipe

    # @staticmethod
    # def find_mutual_matches(user_id):
    #     matches = db.session.query(SwipeRight).filter_by(swiper_id=user_id).all()
    #     match_ids = [match.swipee_id for match in matches]

    #     mutual_matches = db.session.query(User).join(
    #         SwipeRight, User.id == SwipeRight.swiper_id
    #     ).filter(
    #         SwipeRight.swipee_id == user_id,
    #         User.id.in_(match_ids)
    #     ).all()

    #     return mutual_matches
