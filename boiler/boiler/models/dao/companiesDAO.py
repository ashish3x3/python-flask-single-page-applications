from boiler.models.database import db



#Format of post
#{"title":"First Deal","deal_url":"www.flipkart.com","discount":20,"categories":["fashion","apparel"],"description":"dflka","views":20,"upvotes":0,"price_original":"240Rs","price_current":"220Rs","posted_by":22}

def base_company():   
    return {"title":"","deal_url":"","discount":0,"categories":[],"description":"","views":0,"upvotes":0,"price_original":"","price_current":"","posted_by":0}



def add_company(data):
    posts=db.posts
    posts.insert(data)
    return True    

def get_company(query_params):
    return True



