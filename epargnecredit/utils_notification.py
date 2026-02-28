def notifier_validation_versement(user, montant):
    """
    Simulation d'envoi WhatsApp après validation de versement.
    """
    print(f"""
    ===============================
    📲 WhatsApp simulé - YaayESS
    ===============================
    Bonjour {user.nom or user.phone},
    Votre versement de {montant} FCFA a été validé.
    Merci pour votre confiance.
    ===============================
    """)