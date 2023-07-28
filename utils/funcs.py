

def pin_piece(piece, state_var):
    # add pieces related to the article
    state_var.append(piece)


def unpin_piece(article, state_var):
    # unpin the article
    state_var.remove(article)
